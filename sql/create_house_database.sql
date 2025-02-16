BEGIN;


CREATE TABLE IF NOT EXISTS public.house_data
(
    politician_name character varying(50) COLLATE pg_catalog."default",
    doc_id character varying(10) COLLATE pg_catalog."default",
    transaction_type character varying(20) COLLATE pg_catalog."default",
    transaction_date date,
    notification_date date,
    asset_name character varying(300) COLLATE pg_catalog."default",
    asset_ticker character varying(10) COLLATE pg_catalog."default",
    asset_type character(5) COLLATE pg_catalog."default",
    min_amount integer,
    max_amount integer,
    trade_id serial NOT NULL,
    politician_id integer,
    CONSTRAINT house_data_pkey PRIMARY KEY (trade_id)
);

CREATE TABLE IF NOT EXISTS public.politicians
(
    politician_name character varying(50) COLLATE pg_catalog."default",
    politician_id serial NOT NULL,
    CONSTRAINT politicians_pkey PRIMARY KEY (politician_id)
);

ALTER TABLE IF EXISTS public.house_data
    ADD CONSTRAINT fk_house_data_politician FOREIGN KEY (politician_id)
    REFERENCES public.politicians (politician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;

END;