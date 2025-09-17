from abc import abstractmethod


class NewOrganizationHandlerBase:
    """
    The base class for New Organization Handler
    Use by set NEW_ORGANIZATION_HANDLER in Django setting file
    """

    def __init__(self, organization, owner):
        self._organization = organization
        self._owner = owner

    @abstractmethod
    def handle(self):
        pass


class DeleteOrganizationHandlerBase:
    """
    The base class for Delete Organization Handler
    Use by set DELETE_ORGANIZATION_HANDLER in Django setting file
    """

    def __init__(self, organization):
        self._organization = organization

    @abstractmethod
    def handle(self):
        pass
