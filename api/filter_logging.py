import re

USER_ID_PATTERN = re.compile(r"user_id=(\d+)")


def filter_user_id_from_query_parameter(logger, method_name: str, event_dict: dict):
    if query := event_dict.get("query"):
        query: str
        event_dict["query"] = USER_ID_PATTERN.sub("user_id=*", query)

    return event_dict
