def mcpResponseFormatter(response):
    return {"aiResponse": response[-1].content if response else ""}