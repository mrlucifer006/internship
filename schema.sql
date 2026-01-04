CREATE TABLE employee (
    id bigint NOT NULL PRIMARY KEY,
    name text,
    phone text,
    login_id text UNIQUE,
    password text,
    Auth_level text,
    status integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE visitors (
    id bigint NOT NULL PRIMARY KEY,
    name text,
    phone text,
    person_to_visit text,
    reason text,
    has_vehicle boolean,
    vehicle_number text,
    entry_time timestamp with time zone,
    exit_time timestamp with time zone,
    status integer,
    denial_reason text,
    updated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE vehicle (
    id bigint NOT NULL PRIMARY KEY,
    driver_name text,
    veh_reg_no text UNIQUE,
    vehicle_img text,
    destination text,
    "time" timestamp with time zone,
    driver_phone text,
    origin text,
    purchase_no text,
    entry_type text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);