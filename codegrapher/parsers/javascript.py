import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser, Query, QueryCursor, Node
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import asdict

from codegrapher.parsers.base import BaseParser
from codegrapher.models import FunctionInfo

JS_LANGUAGE = Language(tsjavascript.language())
TS_LANGUAGE = Language(tstypescript.language_typescript())

class JSParser(BaseParser):
    def __init__(self, source_code: str, file_path: Path):
        super().__init__(source_code, file_path)
        
        # Determine language based on extension
        if file_path.suffix == '.ts':
            self.language = TS_LANGUAGE
        else:
            self.language = JS_LANGUAGE
            
        self.parser = Parser(self.language)
        
        # JavaScript/TypeScript has multiple ways to define functions
        self.func_query_str = """
        [
            (function_declaration
                name: (identifier) @func.name
                parameters: (formal_parameters) @func.params
                body: (statement_block) @func.body) @func.def
                
            (method_definition
                name: (property_identifier) @func.name
                parameters: (formal_parameters) @func.params
                body: (statement_block) @func.body) @func.def
                
            (variable_declarator
                name: (identifier) @func.name
                value: (arrow_function
                    parameters: _ @func.params
                    body: _ @func.body)) @func.def
                    
            (variable_declarator
                name: (identifier) @func.name
                value: (function_expression
                    parameters: (formal_parameters) @func.params
                    body: (statement_block) @func.body)) @func.def
        ]
        """
        
        self.class_query_str = """
        (class_declaration
            name: (identifier) @class.name
            body: (class_body) @class.body) @class.def
        """
        
        self.call_query_str = """
        (call_expression
            function: [
                (identifier) @call.name
                (member_expression property: (property_identifier) @call.name)
            ]) @call.node
        """
        
        self.func_query = Query(self.language, self.func_query_str)
        self.class_query = Query(self.language, self.class_query_str)
        self.call_query = Query(self.language, self.call_query_str)

    def _get_node_text(self, node: Node) -> str:
        if not node: return ""
        start = node.start_byte
        end = node.end_byte
        return self.source_bytes[start:end].decode('utf-8', errors='ignore')

    def _calculate_complexity(self, body_node: Node) -> int:
        complexity = 1
        def walk(n: Node):
            nonlocal complexity
            if n.type in ['if_statement', 'for_statement', 'while_statement', 'do_statement', 'switch_statement', 'catch_clause', 'ternary_expression', 'logical_and', 'logical_or']:
                complexity += 1
            for child in n.children:
                walk(child)
        walk(body_node)
        return complexity

    def _get_docstring(self, func_node: Node) -> Optional[str]:
        # In JS/TS, JSDoc comments are usually preceding siblings of the function node
        prev = func_node.prev_sibling
        if prev and prev.type == 'comment':
            return self._get_node_text(prev).strip("/* \n\t")
        return None

    def _extract_calls(self, body_node: Node) -> List[str]:
        cursor = QueryCursor(self.call_query)
        matches = cursor.matches(body_node)
        calls = []
        for _, match in matches:
            if 'call.name' in match:
                for node in match['call.name']:
                    calls.append(self._get_node_text(node))
        return list(dict.fromkeys(calls))

    def parse(self) -> Dict[str, Any]:
        tree = self.parser.parse(self.source_bytes)
        
        # 1. Track classes
        cursor = QueryCursor(self.class_query)
        class_matches = cursor.matches(tree.root_node)
        
        class_methods = {}
        for _, match in class_matches:
            if 'class.name' in match and 'class.body' in match:
                class_name = self._get_node_text(match['class.name'][0])
                class_body = match['class.body'][0]
                
                func_cursor = QueryCursor(self.func_query)
                method_matches = func_cursor.matches(class_body)
                for _, mmatch in method_matches:
                    if 'func.name' in mmatch and 'func.def' in mmatch:
                        method_node = mmatch['func.def'][0]
                        class_methods[method_node.id] = class_name
                        
        # 2. Extract functions
        cursor = QueryCursor(self.func_query)
        func_matches = cursor.matches(tree.root_node)
        
        for _, match in func_matches:
            if 'func.def' not in match or 'func.name' not in match: continue
            
            func_node = match['func.def'][0]
            raw_name = self._get_node_text(match['func.name'][0])
            
            class_name = class_methods.get(func_node.id)
            qualified_name = f"{class_name}.{raw_name}" if class_name else raw_name
            
            params_text = ""
            if 'func.params' in match:
                params_text = self._get_node_text(match['func.params'][0]).strip("()")
                
            body_node = match['func.body'][0] if 'func.body' in match else None
            
            complexity = self._calculate_complexity(body_node) if body_node else 1
            docstring = self._get_docstring(func_node)
            calls = self._extract_calls(body_node) if body_node else []
            
            # Check for async
            is_async = 'async' in self._get_node_text(func_node).split()[:2]
            
            self.functions[qualified_name] = asdict(FunctionInfo(
                name=qualified_name,
                calls=calls,
                source_code=self._get_node_text(func_node),
                file_path=str(self.file_path.resolve()),
                complexity=complexity,
                line_number=func_node.start_point[0] + 1,
                is_async=is_async,
                is_method=class_name is not None,
                docstring=docstring,
                signature=params_text
            ))

        return self.functions
