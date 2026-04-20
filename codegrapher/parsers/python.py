import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor, Node
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import asdict

from codegrapher.parsers.base import BaseParser
from codegrapher.models import FunctionInfo

PY_LANGUAGE = Language(tspython.language())

class PythonParser(BaseParser):
    def __init__(self, source_code: str, file_path: Path):
        super().__init__(source_code, file_path)
        self.parser = Parser(PY_LANGUAGE)
        
        self.func_query_str = """
        (function_definition
            name: (identifier) @func.name
            parameters: (parameters) @func.params
            body: (block) @func.body) @func.def
        """
        self.class_query_str = """
        (class_definition
            name: (identifier) @class.name
            body: (block) @class.body) @class.def
        """
        self.call_query_str = """
        (call
            function: [
                (identifier) @call.name
                (attribute attribute: (identifier) @call.name)
            ]) @call.node
        """
        self.func_query = Query(PY_LANGUAGE, self.func_query_str)
        self.class_query = Query(PY_LANGUAGE, self.class_query_str)
        self.call_query = Query(PY_LANGUAGE, self.call_query_str)

    def _get_node_text(self, node: Node) -> str:
        if not node: return ""
        # The new tree-sitter python bindings return bytes from node.text if available,
        # but the standard way is to slice the source bytes
        start = node.start_byte
        end = node.end_byte
        return self.source_bytes[start:end].decode('utf-8', errors='ignore')

    def _calculate_complexity(self, body_node: Node) -> int:
        # A simple complexity calculation based on control flow nodes
        complexity = 1
        
        # Traverse the body node to count if, for, while, etc.
        def walk(n: Node):
            nonlocal complexity
            if n.type in ['if_statement', 'for_statement', 'while_statement', 'try_statement', 'boolean_operator']:
                complexity += 1
            for child in n.children:
                walk(child)
                
        walk(body_node)
        return complexity

    def _get_docstring(self, body_node: Node) -> Optional[str]:
        if not body_node or not body_node.children:
            return None
        first_child = body_node.children[0]
        if first_child.type == 'expression_statement':
            string_node = first_child.children[0]
            if string_node.type == 'string':
                return self._get_node_text(string_node).strip("'\\\"")
        return None

    def _extract_calls(self, body_node: Node) -> List[str]:
        cursor = QueryCursor(self.call_query)
        matches = cursor.matches(body_node)
        calls = []
        for _, match in matches:
            if 'call.name' in match:
                for node in match['call.name']:
                    calls.append(self._get_node_text(node))
        # Deduplicate while preserving order
        return list(dict.fromkeys(calls))

    def parse(self) -> Dict[str, Any]:
        tree = self.parser.parse(self.source_bytes)
        
        # 1. First, find all classes and their methods to track ownership
        cursor = QueryCursor(self.class_query)
        class_matches = cursor.matches(tree.root_node)
        
        class_methods = {}
        for _, match in class_matches:
            if 'class.name' in match and 'class.body' in match:
                class_name = self._get_node_text(match['class.name'][0])
                class_body = match['class.body'][0]
                
                # Query for methods inside the class body
                func_cursor = QueryCursor(self.func_query)
                method_matches = func_cursor.matches(class_body)
                for _, mmatch in method_matches:
                    if 'func.name' in mmatch:
                        method_name = self._get_node_text(mmatch['func.name'][0])
                        method_node = mmatch['func.def'][0]
                        class_methods[method_node.id] = class_name
                        
        # 2. Find all functions (both top-level and methods)
        cursor = QueryCursor(self.func_query)
        func_matches = cursor.matches(tree.root_node)
        
        for _, match in func_matches:
            if 'func.def' not in match or 'func.name' not in match: continue
            
            func_node = match['func.def'][0]
            raw_name = self._get_node_text(match['func.name'][0])
            
            # Check if this function is a method of a class
            class_name = class_methods.get(func_node.id)
            qualified_name = f"{class_name}.{raw_name}" if class_name else raw_name
            
            params_text = ""
            if 'func.params' in match:
                params_text = self._get_node_text(match['func.params'][0]).strip("()")
                
            body_node = match['func.body'][0] if 'func.body' in match else None
            
            complexity = self._calculate_complexity(body_node) if body_node else 1
            docstring = self._get_docstring(body_node) if body_node else None
            calls = self._extract_calls(body_node) if body_node else []
            
            # In tree-sitter, async functions usually have type 'function_definition' but might have an 'async' modifier
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
