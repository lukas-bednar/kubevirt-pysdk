class KubeVirtException(Exception):
    pass


class WaitForException(KubeVirtException):
    pass


class WaitForFailureMatch(WaitForException):
    def __init__(self, event):
        self.event = event

    def __str__(self):
        return "Failure condition satisfied with item: %s" % self.event


class WaitForTimeout(WaitForException):
    def __init__(self, name, timeout):
        self.name = name
        self.timeout = timeout

    def __str__(self):
        return "Waiting for events on %s reached timeout: %ss" % (
            self.name, self.timeout
        )


class EntityNotFound(KubeVirtException):
    def __init__(self, entity, origexc):
        self.entiy = entity
        self.exc = origexc

    def __str__(self):
        return "Entity %s not found.\n%s %s" % (
            self.entiy, self.exc.__class__.__name__, self.exc
        )


class ConflictingEntities(KubeVirtException):
    def __init__(self, entity, origexc):
        self.entiy = entity
        self.exc = origexc

    def __str__(self):
        return "Entity %s has conflict found.\n%s %s" % (
            self.entiy, self.exc.__class__.__name__, self.exc
        )
