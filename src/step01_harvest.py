# src/step01_harvest.py

class HandlerRegistry:
    _handlers = {}

    @classmethod
    def register(cls, name, handler_cls):
        cls._handlers[name] = handler_cls

    @classmethod
    def get_handler(cls, name):
        handler_cls = cls._handlers.get(name)
        if not handler_cls:
            raise ValueError(f"Handler '{name}' not found in registry.")
        return handler_cls()

def harvest_data(handler_name, *args, **kwargs):
    handler = HandlerRegistry.get_handler(handler_name)
    return handler.harvest(*args, **kwargs)

# Example handler implementation
class ExampleHandler:
    def harvest(self, *args, **kwargs):
        print("Harvesting data with ExampleHandler")
        # Add harvesting logic here

# Register the example handler
HandlerRegistry.register('example', ExampleHandler)
