CREATE TABLE IF NOT EXISTS expenses (
    id              SERIAL PRIMARY KEY,
    amount          NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    category        VARCHAR(50) NOT NULL CHECK (category IN (
                        'groceries', 'travel', 'rent', 'student_loan',
                        'shopping', 'food', 'misc'
                    )),
    description     VARCHAR(255),
    expense_date    DATE NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id         INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS anomalies (
    id              SERIAL PRIMARY KEY,
    expense_id      INTEGER NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    reason          VARCHAR(255) NOT NULL,
    rule_triggered  VARCHAR(100) NOT NULL,
    severity        VARCHAR(20)  NOT NULL DEFAULT 'medium',
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_expenses_category_date ON expenses(category, expense_date);
CREATE INDEX IF NOT EXISTS idx_anomalies_expense_id ON anomalies(expense_id);