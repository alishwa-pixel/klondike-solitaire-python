# structures.py  -  our own Stack, Queue and LinkedList (Phases 2 and 3)


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Stack:
    """LIFO. Used for foundation piles, the waste pile and the undo/redo history."""

    def __init__(self):
        self.top = None
        self._size = 0

    def push(self, item):
        node = Node(item)
        node.next = self.top
        self.top = node
        self._size += 1

    def pop(self):
        if self.top is None:
            raise IndexError("pop from empty stack")
        node = self.top
        self.top = node.next
        self._size -= 1
        return node.data

    def peek(self):
        if self.top is None:
            return None
        return self.top.data

    def is_empty(self):
        return self.top is None

    def size(self):
        return self._size

    def to_list(self):
        """Items from bottom to top."""
        items = []
        current = self.top
        while current is not None:
            items.append(current.data)
            current = current.next
        items.reverse()
        return items


class Queue:
    """FIFO. Used for the stockpile (draw pile)."""

    def __init__(self):
        self.head = None   # front: next item to leave
        self.tail = None   # back: last item that joined
        self._size = 0

    def enqueue(self, item):
        node = Node(item)
        if self.tail is None:
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self._size += 1

    def dequeue(self):
        if self.head is None:
            raise IndexError("dequeue from empty queue")
        node = self.head
        self.head = node.next
        if self.head is None:
            self.tail = None
        self._size -= 1
        return node.data

    def peek(self):
        if self.head is None:
            return None
        return self.head.data

    def is_empty(self):
        return self.head is None

    def size(self):
        return self._size

    def to_list(self):
        """Items from front to back."""
        items = []
        current = self.head
        while current is not None:
            items.append(current.data)
            current = current.next
        return items


class LinkedList:
    """Singly linked list. Used for the 7 tableau piles because we must be
    able to cut a whole run of cards off the middle/end of a pile.
    It also gives stack-style access to the END of the pile (push, pop, peek),
    because only the top (last) card of a tableau pile is playable."""

    def __init__(self):
        self.head = None
        self._size = 0

    def append(self, item):
        node = Node(item)
        if self.head is None:
            self.head = node
        else:
            current = self.head
            while current.next is not None:
                current = current.next
            current.next = node
        self._size += 1

    def extend(self, items):
        for item in items:
            self.append(item)

    def last(self):
        if self.head is None:
            return None
        current = self.head
        while current.next is not None:
            current = current.next
        return current.data

    def split_from(self, index):
        """Cut the list at `index`. Removes and returns items from index to the end."""
        if index < 0 or index >= self._size:
            raise IndexError("index out of range")
        removed = []
        if index == 0:
            current = self.head
            self.head = None
        else:
            before = self.head
            for _ in range(index - 1):
                before = before.next
            current = before.next
            before.next = None
        while current is not None:
            removed.append(current.data)
            current = current.next
        self._size = index
        return removed

    # ---- stack-style operations on the top (last) card of the pile
    def push(self, item):
        self.append(item)

    def pop(self):
        return self.remove_last()

    def peek(self):
        return self.last()

    def remove_last(self):
        if self._size == 0:
            raise IndexError("remove from empty list")
        return self.split_from(self._size - 1)[0]

    def is_empty(self):
        return self.head is None

    def size(self):
        return self._size

    def to_list(self):
        items = []
        current = self.head
        while current is not None:
            items.append(current.data)
            current = current.next
        return items
