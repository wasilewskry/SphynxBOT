-- SQLITE

CREATE TABLE IF NOT EXISTS users
(
    id INTEGER, -- User's Discord ID.
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS reminders
(
    user_id            INTEGER NOT NULL,
    channel_id         INTEGER,          -- Where to post the reminder. Send as a private message if NULL.
    type               TEXT,             -- Reminder type.
    creation_timestamp INTEGER NOT NULL, -- When created.
    reminder_timestamp INTEGER NOT NULL, -- When to send the reminder.
    description        TEXT    NOT NULL, -- Text body of the reminder.
    PRIMARY KEY (user_id, creation_timestamp),
    FOREIGN KEY (user_id) REFERENCES users (id)
);