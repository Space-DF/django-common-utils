from abc import ABC, abstractmethod


class TaskHandlerBase(ABC):
    @abstractmethod
    def handle(self, *args, **kwargs):
        raise NotImplementedError("Method must be implemented")


class TaskProcessorBase:
    @abstractmethod
    def process(self, *args, **kwargs):
        raise NotImplementedError("Method must be implemented")
