CREATE SCHEMA IF NOT EXISTS calc_schema;

CREATE TABLE IF NOT EXISTS calc_schema.calc_results (
    id SERIAL PRIMARY KEY,
    total_cost_rub NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);