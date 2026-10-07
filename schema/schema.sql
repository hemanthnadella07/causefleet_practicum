DROP TABLE IF EXISTS interactions;
DROP TABLE IF EXISTS gifts;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS goals;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS donors;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS org_profile;

CREATE TABLE org_profile (
    org_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    sector VARCHAR(64) NOT NULL,
    annual_budget DECIMAL(14, 2) NOT NULL,
    fiscal_year_start DATE NOT NULL,
    is_synthetic_label BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE staff (
    staff_id VARCHAR(32) PRIMARY KEY,
    org_id VARCHAR(32) NOT NULL,
    full_name VARCHAR(64) NOT NULL,
    title VARCHAR(64) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    role VARCHAR(32) NOT NULL,
    FOREIGN KEY (org_id) REFERENCES org_profile(org_id) ON DELETE CASCADE
);

CREATE TABLE donors (
    donor_id VARCHAR(32) PRIMARY KEY,
    org_id VARCHAR(32) NOT NULL,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    phone VARCHAR(32),
    address VARCHAR(128),
    city VARCHAR(64),
    state VARCHAR(8),
    zip_code VARCHAR(16),
    donor_tier VARCHAR(16) CHECK (donor_tier IN ('Small', 'Mid', 'Major')),
    created_at DATE NOT NULL,
    is_synthetic_label BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (org_id) REFERENCES org_profile(org_id) ON DELETE CASCADE
);

CREATE TABLE campaigns (
    campaign_id VARCHAR(32) PRIMARY KEY,
    org_id VARCHAR(32) NOT NULL,
    name VARCHAR(128) NOT NULL,
    goal_amount DECIMAL(14, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    channel VARCHAR(32) NOT NULL,
    FOREIGN KEY (org_id) REFERENCES org_profile(org_id) ON DELETE CASCADE
);

CREATE TABLE goals (
    goal_id VARCHAR(32) PRIMARY KEY,
    campaign_id VARCHAR(32) NOT NULL,
    target_metric VARCHAR(64) NOT NULL,
    target_value DECIMAL(14, 2) NOT NULL,
    deadline DATE NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE
);

CREATE TABLE events (
    event_id VARCHAR(32) PRIMARY KEY,
    campaign_id VARCHAR(32) NOT NULL,
    event_name VARCHAR(128) NOT NULL,
    event_date DATE NOT NULL,
    ticket_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE
);

CREATE TABLE gifts (
    gift_id VARCHAR(32) PRIMARY KEY,
    donor_id VARCHAR(32) NOT NULL,
    campaign_id VARCHAR(32) NOT NULL,
    amount DECIMAL(14, 2) NOT NULL CHECK (amount > 0),
    gift_date DATE NOT NULL,
    payment_channel VARCHAR(32) NOT NULL,
    is_pledge BOOLEAN NOT NULL DEFAULT 0,
    status VARCHAR(16) NOT NULL DEFAULT 'Completed',
    FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE RESTRICT
);

CREATE TABLE interactions (
    interaction_id VARCHAR(32) PRIMARY KEY,
    donor_id VARCHAR(32) NOT NULL,
    staff_id VARCHAR(32) NOT NULL,
    interaction_date DATE NOT NULL,
    type VARCHAR(64) NOT NULL,
    notes TEXT,
    FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE RESTRICT
);

CREATE INDEX idx_gifts_donor ON gifts(donor_id);
CREATE INDEX idx_gifts_date ON gifts(gift_date);
CREATE INDEX idx_gifts_campaign ON gifts(campaign_id);