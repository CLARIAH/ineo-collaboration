class BidirectionalMap:
    def __init__(self):
        self.forward = {}
        self.backward = {}

    def insert(self, key, value):
        if not key in self.forward:
            self.forward[key] = value
            self.backward[value] = key

    def remove_by_key(self, key):
        if key in self.forward:
            value = self.forward.pop(key)
            del self.backward[value]

    def remove_by_value(self, value):
        if value in self.backward:
            key = self.backward.pop(value)
            del self.forward[key]

    def get_by_key(self, key):
        return self.forward.get(key)

    def get_by_value(self, value):
        return self.backward.get(value)

    def __repr__(self):
        return f"Forward: {self.forward}\nBackward: {self.backward}"

"""
# Example usage:
bimap = BidirectionalMap()
bimap.insert('a', 1)
bimap.insert('b', 2)
print(bimap.get_by_key('a'))  # Output: 1
print(bimap.get_by_value(2))  # Output: 'b'
"""