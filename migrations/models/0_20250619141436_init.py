from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "bank_accounts" (
    "id" UUID NOT NULL PRIMARY KEY,
    "number" VARCHAR(20) NOT NULL,
    "bank_name" VARCHAR(255) NOT NULL,
    "bank_bic" VARCHAR(9) NOT NULL,
    "bank_corr_account" VARCHAR(20) NOT NULL,
    "legal_entity_id" UUID NOT NULL
);
CREATE TABLE IF NOT EXISTS "contract_statuses" (
    "id" VARCHAR(255) NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "contracts" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "date" BIGINT NOT NULL,
    "buyer_id" UUID NOT NULL,
    "seller_id" UUID NOT NULL,
    "comment" TEXT,
    "s3_key" VARCHAR(255),
    "company_id" UUID NOT NULL,
    "status_id" VARCHAR(255) NOT NULL REFERENCES "contract_statuses" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "acts" (
    "id" UUID NOT NULL PRIMARY KEY,
    "number" VARCHAR(255) NOT NULL,
    "date" BIGINT NOT NULL,
    "buyer_id" UUID NOT NULL,
    "seller_id" UUID NOT NULL,
    "company_id" UUID NOT NULL,
    "contract_id" UUID REFERENCES "contracts" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "bills" (
    "id" UUID NOT NULL PRIMARY KEY,
    "number" VARCHAR(255) NOT NULL,
    "date" BIGINT NOT NULL,
    "buyer_id" UUID NOT NULL,
    "seller_id" UUID NOT NULL,
    "company_id" UUID NOT NULL,
    "bank_account_id" UUID NOT NULL REFERENCES "bank_accounts" ("id") ON DELETE CASCADE,
    "contract_id" UUID REFERENCES "contracts" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "entity_company_relations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "company_id" UUID NOT NULL,
    "legal_entity_id" UUID NOT NULL,
    "relation_type" VARCHAR(10) NOT NULL,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "services" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "company_id" UUID NOT NULL
);
CREATE TABLE IF NOT EXISTS "act_details" (
    "id" UUID NOT NULL PRIMARY KEY,
    "quantity" DECIMAL(8,3) NOT NULL,
    "summ" DECIMAL(10,2) NOT NULL,
    "price" DECIMAL(8,2) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "act_id" UUID NOT NULL REFERENCES "acts" ("id") ON DELETE CASCADE,
    "service_id" UUID NOT NULL REFERENCES "services" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "bill_details" (
    "id" UUID NOT NULL PRIMARY KEY,
    "quantity" DECIMAL(8,3) NOT NULL,
    "summ" DECIMAL(10,2) NOT NULL,
    "price" DECIMAL(8,2) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "bill_id" UUID NOT NULL REFERENCES "bills" ("id") ON DELETE CASCADE,
    "service_id" UUID NOT NULL REFERENCES "services" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "templates" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "company_id" UUID NOT NULL,
    "description" TEXT,
    "entity" VARCHAR(50) NOT NULL,
    "s3_key" VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
