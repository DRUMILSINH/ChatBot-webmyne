class LogRouter:
    """
    Route legacy ingestion log tables to `logs`, while runtime chat tables live in
    `default` with Django auth/session tables.
    """

    LOGS_MODELS = {"personalinfo", "chatlog", "clickedurl"}
    DEFAULT_MODELS = {"chatsession", "chatmessage", "auditlog", "crawljob", "messagefeedback"}

    def _chat_target_db(self, model_name: str) -> str:
        normalized = model_name.lower()
        if normalized in self.LOGS_MODELS:
            return "logs"
        if normalized in self.DEFAULT_MODELS:
            return "default"
        # Safe fallback for any future `chat` model.
        return "default"

    def db_for_read(self, model, **hints):
        if model._meta.app_label == "chat":
            return self._chat_target_db(model.__name__)
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "chat":
            return self._chat_target_db(model.__name__)
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == "chat" and obj2._meta.app_label == "chat":
            return self._chat_target_db(obj1.__class__.__name__) == self._chat_target_db(obj2.__class__.__name__)
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label != "chat":
            return db == "default"

        if model_name is None:
            # Allow chat app non-model operations on both databases.
            return db in {"default", "logs"}

        return db == self._chat_target_db(model_name)
