from abc import ABC, abstractmethod

my_list = [1, 2, 3, 4, 5, 6]

class A:
    def __new__(cls, get_list, *args, **kwargs):  # run before __init__
        if len(get_list) > 5:
            return super().__new__(cls, *args, **kwargs)
        else:
            return None

    def __init__(self, get_list: list):
        self.my_list = get_list
    def __iter__(self):
        for number in self.my_list:
            yield number

    def __next__(self):
        list_copy = self.my_list.copy()
        list_copy.reverse()
        if list_copy:
            return list_copy.pop()
        else:
            return StopIteration

    def __call__(self, *args, **kwargs):
        print(f'Your List: {self.my_list}')


# design pattern ------------------------------


class InsideDesignPattern:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, name):
        self.name = name


class Singleton(type):
    _instance = None

    def __call__(self, *args, **kwargs):
        if not self._instance:
            self._instance = super().__call__(*args, **kwargs)
        return self._instance


class JustOneInstance(metaclass=Singleton):
    def __init__(self, naem):
        print(naem)


# -------------------------------------

class Abbstact(ABC):  # declare abstract class
    def one(self):
        pass

    @abstractmethod
    def two(self):
        pass

class Abstact2(Abbstact):
    def two(self):
        pass


class FactoryDesignPattern(ABC):
    @abstractmethod
    def hello(self):
        pass

    def get_hello(self):
        return self.hello()


class FactoryUse(FactoryDesignPattern):
    def hello(self):
        return 'ok'

# a = FactoryUse()
# print(a.get_hello())
