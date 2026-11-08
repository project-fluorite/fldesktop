from fldesktop.include.fs3.db import Database


class Resolver:
    def __init__(self, core, db: Database):

        self.core = core
        self.db = db

    def create_node(self, attrs: dict):

        return self.db.create_node(attrs)

    def delete_node(self, id: int):

        self.db.delete_node(id)

    def set_attrs(self, id: int, attrs: dict):

        self.db.set_attrs(id, attrs)

    def del_attrs(self, id: int, attrs: list):

        oldattrs = self.db.get_node(id)
        newattrs = {k: v for k, v in oldattrs.items() if k not in attrs}
        self.db.set_attrs(id, newattrs)

    def get_attr(self, id: int, attr: str):

        nodeattrs = self.db.get_node(id)
        if attr in nodeattrs:
            return nodeattrs[attr]

    def get_attrs(self, id: int):

        return self.db.get_node(id)

    def query(self, filters: list):

        return self.db.query(filters)

    def open(self, id: int):

        return self.db.open(id)