from collections import deque
from heapq import heappop, heappush
from typing import (Any, Callable, Deque, Dict, Generic, Iterable, List,
                    Optional, Sequence, Set, Tuple, TypeVar)

from typing_extensions import Protocol

T = TypeVar("T")


def linear_contains(iterable: Iterable[T], key: T) -> bool:
    return key in iterable


C = TypeVar("C", bound="Comparable")


class Comparable(Protocol):
    def __eq__(self, other: Any) -> bool:
        ...

    def __lt__(self: C, other: C) -> bool:
        ...

    def __gt__(self: C, other: C) -> bool:
        return (not self < other) and self != other

    def __le__(self: C, other: C) -> bool:
        return self < other or self == other

    def __ge__(self: C, other: C) -> bool:
        return not self < other


def binary_contains(sequence: Sequence[C], key: C) -> bool:
    low: int = 0
    high: int = len(sequence) - 1
    while low <= high:
        mid: int = (low + high) // 2
        if sequence[mid] < key:
            low = mid + 1
        elif sequence[mid] > key:
            high = mid - 1
        else:
            return True
    return False


class Node(Generic[T]):
    def __init__(
        self,
        state: T,
        parent: Optional["Node"],
        cost: float = 0.0,
        heuristic: float = 0.0,
    ) -> None:
        self.state: T = state
        self.parent: Optional[Node] = parent
        self.cost: float = cost
        self.heuristic: float = heuristic

    def __lt__(self, other: "Node") -> bool:
        return (self.cost + self.heuristic) < (other.cost + other.heuristic)


def node_to_path(node: Node[T]) -> List[T]:
    path: List[T] = [node.state]
    while node.parent is not None:
        node = node.parent
        path.append(node.state)
    path.reverse()
    return path


class Stack(Generic[T]):
    def __init__(self) -> None:
        self._container: List[T] = []

    @property
    def empty(self):
        return not self._container

    def push(self, item: T) -> None:
        self._container.append(item)

    def pop(self) -> T:
        return self._container.pop()  # LIFO

    def __repr__(self) -> str:
        return repr(self._container)


class Queue(Generic[T]):
    def __init__(self) -> None:
        self._container: Deque[T] = deque()

    @property
    def empty(self) -> bool:
        return not self._container

    def push(self, item: T) -> None:
        self._container.append(item)

    def pop(self) -> T:
        return self._container.popleft()  # FIFO

    def __repr__(self) -> str:
        return repr(self._container)


class PriorityQueue(Generic[T]):
    def __init__(self) -> None:
        self._container: List[T] = []

    @property
    def empty(self) -> bool:
        return not self._container

    def push(self, item: T) -> None:
        heappush(self._container, item)  # in by priority

    def pop(self) -> T:
        return heappop(self._container)  # out by priority

    def __repr__(self):
        return repr(self._container)


def _first_search(
    frontier,
    initial: T,
    goal_test: Callable[[T], bool],
    successors: Callable[[T], List[T]],
) -> Tuple[Optional[Node[T]], int]:
    frontier.push(Node(initial, None))
    explored: Set[T] = {initial}

    while not frontier.empty:
        current_node: Node[T] = frontier.pop()
        current_state: T = current_node.state
        if goal_test(current_state):
            return current_node, len(explored)
        for child in successors(current_state):
            if child not in explored:
                explored.add(child)
                frontier.push(Node(child, current_node))
    return None, len(explored)


def dfs(
    initial: T,
    goal_test: Callable[[T], bool],
    successors: Callable[[T], List[T]],
) -> Tuple[Optional[Node[T]], int]:
    frontier: Stack[Node[T]] = Stack()
    return _first_search(frontier, initial, goal_test, successors)


def bfs(
    initial: T,
    goal_test: Callable[[T], bool],
    successors: Callable[[T], List[T]],
) -> Tuple[Optional[Node[T]], int]:
    frontier: Queue[Node[T]] = Queue()
    return _first_search(frontier, initial, goal_test, successors)


def astar(
    initial: T,
    goal_test: Callable[[T], bool],
    successors: Callable[[T], List[T]],
    heuristic: Callable[[T], float],
) -> Tuple[Optional[Node[T]], int]:
    frontier: PriorityQueue[Node[T]] = PriorityQueue()
    frontier.push(Node(initial, None, 0.0, heuristic(initial)))
    explored: Dict[T, float] = {initial: 0.0}

    while not frontier.empty:
        current_node: Node[T] = frontier.pop()
        current_state: T = current_node.state
        if goal_test(current_state):
            return current_node, len(explored)
        for child in successors(current_state):
            new_cost: float = current_node.cost + 1
            if child not in explored or explored[child] > new_cost:
                explored[child] = new_cost
                frontier.push(
                    Node(child, current_node, new_cost, heuristic(child))
                )
    return None, len(explored)
