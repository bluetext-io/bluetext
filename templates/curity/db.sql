CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE delegations (
  id                        VARCHAR(40)   PRIMARY KEY,
  owner                     VARCHAR(128)  NOT NULL,
  created                   BIGINT        NOT NULL,
  expires                   BIGINT        NOT NULL,
  scope                     VARCHAR(1000) NULL,
  scope_claims              TEXT          NULL,
  client_id                 VARCHAR(128)  NOT NULL,
  redirect_uri              VARCHAR(512)  NULL,
  status                    VARCHAR(16)   NOT NULL,
  claims                    TEXT          NULL,
  authentication_attributes TEXT          NULL,
  authorization_code_hash   VARCHAR(89)   NULL
);

CREATE INDEX IDX_DELEGATIONS_CLIENT_ID               ON delegations (client_id ASC);
CREATE INDEX IDX_DELEGATIONS_STATUS                  ON delegations (status ASC);
CREATE INDEX IDX_DELEGATIONS_EXPIRES                 ON delegations (expires ASC);
CREATE INDEX IDX_DELEGATIONS_OWNER                   ON delegations (owner ASC);
CREATE INDEX IDX_DELEGATIONS_AUTHORIZATION_CODE_HASH ON delegations (authorization_code_hash ASC);

CREATE TABLE tokens (
  token_hash     VARCHAR(89)   NOT NULL PRIMARY KEY,
  id             VARCHAR(64)   NULL,
  delegations_id VARCHAR(40)   NOT NULL ,
  purpose        VARCHAR(32)   NOT NULL,
  usage          VARCHAR(8)    NOT NULL,
  format         VARCHAR(32)   NOT NULL,
  created        BIGINT        NOT NULL,
  expires        BIGINT        NOT NULL,
  scope          VARCHAR(1000) NULL,
  scope_claims   TEXT          NULL,
  status         VARCHAR(16)   NOT NULL,
  issuer         VARCHAR(200)  NOT NULL,
  subject        VARCHAR(64)   NOT NULL,
  audience       VARCHAR(512)  NULL,
  not_before     BIGINT        NULL,
  claims         TEXT          NULL,
  meta_data      TEXT          NULL
);

CREATE INDEX IDX_TOKENS_ID      ON tokens (id);
CREATE INDEX IDX_TOKENS_STATUS  ON tokens (status ASC);
CREATE INDEX IDX_TOKENS_EXPIRES ON tokens (expires ASC);

CREATE TABLE nonces (
  token           VARCHAR(64) NOT NULL PRIMARY KEY,
  reference_data  TEXT        NOT NULL,
  created         BIGINT      NOT NULL,
  ttl             BIGINT      NOT NULL,
  consumed        BIGINT      NULL,
  status          VARCHAR(16) NOT NULL DEFAULT 'issued'
);

CREATE TABLE accounts (
  account_id  VARCHAR(64)   PRIMARY KEY NOT NULL DEFAULT uuid_generate_v4(),
  username    VARCHAR(64)   NOT NULL,
  password    VARCHAR(128),
  email       VARCHAR(64),
  phone       VARCHAR(32),
  attributes  JSONB,
  active      SMALLINT      NOT NULL DEFAULT 0,
  created     BIGINT        NOT NULL,
  updated     BIGINT        NOT NULL
);

CREATE UNIQUE INDEX IDX_ACCOUNTS_USERNAME ON accounts (username);
CREATE UNIQUE INDEX IDX_ACCOUNTS_PHONE    ON accounts (phone);
CREATE UNIQUE INDEX IDX_ACCOUNTS_EMAIL    ON accounts (email);
CREATE INDEX IDX_ACCOUNTS_ATTRIBUTES_NAME ON accounts USING GIN ( (attributes->'name') );

CREATE TABLE linked_accounts (
  account_id                  VARCHAR(64),
  linked_account_id           VARCHAR(64) NOT NULL,
  linked_account_domain_name  VARCHAR(64) NOT NULL,
  linking_account_manager     VARCHAR(128),
  created                     TIMESTAMP   NOT NULL,

  PRIMARY KEY (linked_account_id, linked_account_domain_name)
);

CREATE INDEX IDX_LINKED_ACCOUNTS_ACCOUNTS_ID ON linked_accounts (account_id ASC);

CREATE TABLE credentials (
  id          VARCHAR(36)  PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject     VARCHAR(64)  NOT NULL,
  password    VARCHAR(128) NOT NULL,
  attributes  JSONB        NOT NULL,
  created     TIMESTAMP    NOT NULL,
  updated     TIMESTAMP    NOT NULL
);

CREATE UNIQUE INDEX IDX_CREDENTIALS_SUBJECT ON credentials (subject);

CREATE TABLE sessions (
  id            VARCHAR(64) NOT NULL PRIMARY KEY,
  session_data  TEXT        NOT NULL,
  expires       BIGINT      NOT NULL
);

CREATE INDEX IDX_SESSIONS_ID         ON sessions (id ASC);
CREATE INDEX IDX_SESSIONS_ID_EXPIRES ON sessions (id, expires);

CREATE TABLE devices (
  id          VARCHAR(64) PRIMARY KEY NOT NULL,
  device_id   VARCHAR(64),
  account_id  VARCHAR(256),
  external_id VARCHAR(32),
  alias       VARCHAR(30),
  form_factor VARCHAR(10),
  device_type VARCHAR(50),
  owner       VARCHAR(256),
  attributes  JSONB,
  expires     BIGINT,
  created     BIGINT      NOT NULL,
  updated     BIGINT      NOT NULL
);

CREATE INDEX IDX_DEVICES_ACCOUNT_ID                   ON devices (account_id ASC);
CREATE UNIQUE INDEX IDX_DEVICES_DEVICE_ID_ACCOUNT_ID  ON devices (device_id ASC, account_id ASC);

CREATE TABLE audit (
  id                    VARCHAR(64)   PRIMARY KEY,
  instant               TIMESTAMP     NOT NULL,
  event_instant         VARCHAR(64)   NOT NULL,
  server                VARCHAR(255)  NOT NULL,
  message               TEXT          NOT NULL,
  event_type            VARCHAR(48)   NOT NULL,
  subject               VARCHAR(128),
  client                VARCHAR(128),
  resource              VARCHAR(128),
  authenticated_subject VARCHAR(128),
  authenticated_client  VARCHAR(128),
  acr                   VARCHAR(128),
  endpoint              VARCHAR(255),
  session               VARCHAR(128)
);

CREATE TABLE dynamically_registered_clients (
  client_id           VARCHAR(64)     NOT NULL PRIMARY KEY,
  client_secret       VARCHAR(128),
  instance_of_client  VARCHAR(64)     NULL,
  created             TIMESTAMP       NOT NULL,
  updated             TIMESTAMP       NOT NULL,
  initial_client      VARCHAR(64)     NULL,
  authenticated_user  VARCHAR(64)     NULL,
  attributes          JSONB           NOT NULL DEFAULT '{}',
  status              VARCHAR(12)     NOT NULL DEFAULT 'active',
  scope               TEXT            NULL,
  redirect_uris       TEXT            NULL,
  grant_types         VARCHAR(500)    NULL
);

CREATE INDEX IDX_DRC_INSTANCE_OF_CLIENT ON dynamically_registered_clients(instance_of_client);
CREATE INDEX IDX_DRC_ATTRIBUTES         ON dynamically_registered_clients USING GIN (attributes);
CREATE INDEX IDX_DRC_CREATED            ON dynamically_registered_clients(created);
CREATE INDEX IDX_DRC_STATUS             ON dynamically_registered_clients(status);
CREATE INDEX IDX_DRC_AUTHENTICATED_USER ON dynamically_registered_clients(authenticated_user);

CREATE TABLE database_clients
(
    client_id                VARCHAR(64)  NOT NULL,
    profile_id               VARCHAR(64)  NOT NULL,
    client_name              VARCHAR(128) NULL,
    created                  TIMESTAMP    NOT NULL,
    updated                  TIMESTAMP    NOT NULL,
    owner                    VARCHAR(128) NOT NULL,
    status                   VARCHAR(16)  NOT NULL DEFAULT 'active',
    client_metadata          JSONB        NOT NULL DEFAULT '{}',
    configuration_references JSONB        NOT NULL DEFAULT '{}',
    attributes               JSONB        NOT NULL DEFAULT '{}',

    PRIMARY KEY (client_id, profile_id)
);

CREATE INDEX IDX_DATABASE_CLIENTS_PROFILE_ID         ON database_clients (profile_id ASC);
CREATE INDEX IDX_DATABASE_CLIENTS_CLIENT_NAME        ON database_clients (client_name ASC);
CREATE INDEX IDX_DATABASE_CLIENTS_OWNER              ON database_clients (owner ASC);
CREATE INDEX IDX_DATABASE_CLIENTS_METADATA_TAGS      ON database_clients USING GIN ((client_metadata -> 'tags') jsonb_path_ops);
CREATE INDEX IDX_DATABASE_CLIENTS_METADATA_TAGS_NULL ON database_clients (client_metadata) WHERE client_metadata->'tags' IS NULL;

CREATE TABLE buckets (
    subject    VARCHAR(128) NOT NULL,
    purpose    VARCHAR(64)  NOT NULL,
    attributes JSONB        NOT NULL,
    created    TIMESTAMP    NOT NULL,
    updated    TIMESTAMP    NOT NULL,

    PRIMARY KEY (subject, purpose)
);

CREATE INDEX IDX_BUCKETS_ATTRIBUTES ON buckets USING GIN (attributes);
