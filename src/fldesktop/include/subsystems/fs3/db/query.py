import logging


def get_related_from(db, node1, node):

    rels = db.querier.query([
        {"op": "=", "attr": "Attr.System.Type", "value": "Node.Relation"},
        {"op": "=", "attr": "Attr.Relation.To", "value": node1},
        {"op": "=", "attr": "Attr.Relation.From", "value": node}
    ])

    return bool(rels)

def get_related_to(db, node1, node):

    rels = db.querier.query([
        {"op": "=", "attr": "Attr.System.Type", "value": "Node.Relation"},
        {"op": "=", "attr": "Attr.Relation.To", "value": node},
        {"op": "=", "attr": "Attr.Relation.From", "value": node1}
    ])

    return bool(rels)

def intersect(lists: list) -> list:
    if not lists:
        return []
    if len(lists) == 1:
        return list(lists[0])
    
    result = set(lists[0])
    for lst in lists[1:]:
        result &= set(lst)
        if not result:
            break
    return list(result)


ADV_OPS = {
    "related_from": get_related_from,
    "related_to": get_related_to
}
ADV_OPS_PARAMS = {
    "related_from": {
        "node": str
    },
    "related_to": {
        "node": str
    }
}


SIMPLE_OPS = {
    "contains": lambda a, b: str(b) in str(a),
    "startswith": lambda a, b: str(a).startswith(str(b)),
    "endswith": lambda a, b: str(a).endswith(str(b)),
    "=": lambda a, b: a == b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b
}


class QueryEngine:
    def __init__(self, db):

        self.db = db

    def filter_node(self, node_id: str, filter: dict):
        attrs = self.db.db[node_id].attrs

        if not "op" in filter:
            return

        if filter["op"] in SIMPLE_OPS:
            if not ("attr" in filter and "value" in filter):
                return False
            if not filter["attr"] in attrs:
                return False

            attr = attrs[filter["attr"]]

            try:
                return SIMPLE_OPS[filter["op"]](attr, filter["value"])
            except Exception as e:
                logging.warning(f"Failed to filter node {node_id}: {str(e)}")
                return False

        elif filter["op"] in ADV_OPS:
            to_pass = {}
            for param, ptype in ADV_OPS_PARAMS[filter["op"]].items():
                if not param in filter:
                    return False
                if not isinstance(filter[param], ptype):
                    return False
                to_pass[param] = filter[param]

            try:
                return ADV_OPS[filter["op"]](self.db, node_id, **to_pass)
            except Exception as e:
                logging.warning(f"Failed to filter node {node_id}: {str(e)}")
                return False

        else:
            return False

    def process_filter(self, filter: dict):

        if not isinstance(filter, dict):
            return []

        r = []

        for node in self.db.db:
            if self.filter_node(node, filter):
                r.append(node)

        return r

    def query(self, filters: list):

        if not isinstance(filters, list):
            return []

        filtered = []

        for filter in filters:
            filtered.append(self.process_filter(filter))

        print("filtered", filtered)

        return intersect(filtered)