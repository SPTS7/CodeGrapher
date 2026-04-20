"""A dummy project fixture for testing the analyzer."""

def func_a(x: int, y: int = 10) -> int:
    """
    This is function A.
    
    It calls func_b.
    """
    return func_b(x) + y

def func_b(val):
    """Function B."""
    return val * 2

class DummyClass:
    """A dummy class."""
    
    def method_one(self):
        """Method 1."""
        func_a(5)
        self.method_two()
        
    def method_two(self):
        """Method 2."""
        pass

def main():
    """Main entry point."""
    func_a(1)
    obj = DummyClass()
    obj.method_one()
