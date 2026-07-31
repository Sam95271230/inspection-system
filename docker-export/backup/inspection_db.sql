--
-- PostgreSQL database dump
--

\restrict CehBmTBKOyjtXchjn1EyzbZXWTq9shd2OjFBQ9Ckn2Py7lkpLN3Tg4DReLqLAkl

-- Dumped from database version 15.15
-- Dumped by pg_dump version 15.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO inspection_user;

--
-- Name: exception_history; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.exception_history (
    id uuid NOT NULL,
    ticket_id uuid NOT NULL,
    from_status character varying(32),
    to_status character varying(32) NOT NULL,
    operator_id uuid NOT NULL,
    action character varying(64) NOT NULL,
    remark text,
    attachment_urls character varying[],
    created_at timestamp without time zone
);


ALTER TABLE public.exception_history OWNER TO inspection_user;

--
-- Name: exception_ticket; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.exception_ticket (
    id uuid NOT NULL,
    inspection_id uuid NOT NULL,
    plant_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    status character varying(32),
    current_assignee_id uuid,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.exception_ticket OWNER TO inspection_user;

--
-- Name: inspection; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.inspection (
    id uuid NOT NULL,
    serial_no character varying(32),
    plant_id uuid NOT NULL,
    line_id uuid NOT NULL,
    station_id uuid NOT NULL,
    ip_address character varying(15) NOT NULL,
    antivirus_status character varying(32) NOT NULL,
    domain_status character varying(32) NOT NULL,
    remark text,
    status character varying(32),
    inspector_id uuid NOT NULL,
    inspect_time timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.inspection OWNER TO inspection_user;

--
-- Name: inspection_image; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.inspection_image (
    id uuid NOT NULL,
    inspection_id uuid NOT NULL,
    file_name character varying(255) NOT NULL,
    storage_key character varying(512) NOT NULL,
    file_size character varying(64),
    mime_type character varying(64),
    sort_order character varying(64)
);


ALTER TABLE public.inspection_image OWNER TO inspection_user;

--
-- Name: line; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.line (
    id uuid NOT NULL,
    plant_id uuid NOT NULL,
    code character varying(32) NOT NULL,
    name character varying(64) NOT NULL
);


ALTER TABLE public.line OWNER TO inspection_user;

--
-- Name: plant; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.plant (
    id uuid NOT NULL,
    code character varying(32) NOT NULL,
    name character varying(64) NOT NULL
);


ALTER TABLE public.plant OWNER TO inspection_user;

--
-- Name: role; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.role (
    id uuid NOT NULL,
    code character varying(32) NOT NULL,
    name character varying(64) NOT NULL,
    description character varying(255)
);


ALTER TABLE public.role OWNER TO inspection_user;

--
-- Name: station; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.station (
    id uuid NOT NULL,
    line_id uuid NOT NULL,
    code character varying(32) NOT NULL,
    name character varying(64) NOT NULL
);


ALTER TABLE public.station OWNER TO inspection_user;

--
-- Name: sys_user; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.sys_user (
    id uuid NOT NULL,
    username character varying(64) NOT NULL,
    password_hash character varying(255) NOT NULL,
    real_name character varying(64),
    mobile character varying(20),
    is_active boolean,
    is_superadmin boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.sys_user OWNER TO inspection_user;

--
-- Name: user_plant; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.user_plant (
    user_id uuid NOT NULL,
    plant_id uuid NOT NULL
);


ALTER TABLE public.user_plant OWNER TO inspection_user;

--
-- Name: user_role; Type: TABLE; Schema: public; Owner: inspection_user
--

CREATE TABLE public.user_role (
    user_id uuid NOT NULL,
    role_id uuid NOT NULL
);


ALTER TABLE public.user_role OWNER TO inspection_user;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.alembic_version (version_num) FROM stdin;
210fb62aebc3
\.


--
-- Data for Name: exception_history; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.exception_history (id, ticket_id, from_status, to_status, operator_id, action, remark, attachment_urls, created_at) FROM stdin;
5d905941-bd9b-435d-b03e-0bdb94da7f3a	0f2ead54-cbef-4b0f-a543-89e03d21eb67	PENDING	PROCESSING	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	ASSIGN	测试，未安装防毒	{}	2026-07-29 06:52:36.568002
b54f82d8-b472-438f-9dd4-3b7a160234bb	0f2ead54-cbef-4b0f-a543-89e03d21eb67	PROCESSING	PENDING_SIGNOFF	3cd97fb7-2993-410d-9c66-bbfbcd00fba3	PROCESS	已处理完成。	{}	2026-07-29 06:53:30.777239
d2bed5f5-941f-4f2e-b26c-fb25d33b3739	0f2ead54-cbef-4b0f-a543-89e03d21eb67	PENDING_SIGNOFF	CLOSED	3cd97fb7-2993-410d-9c66-bbfbcd00fba3	APPROVE		{}	2026-07-29 06:53:45.733043
37968760-fb20-4c48-a83b-bc29a4b5ffec	9f06d542-df8f-46cf-9cd0-d30f3609964f	PENDING	PROCESSING	3cd97fb7-2993-410d-9c66-bbfbcd00fba3	ASSIGN		{}	2026-07-29 06:54:52.400749
abd9b02f-b162-4c8b-b34c-3e280d4e3eaa	8b52c741-e068-4393-aa90-798e4324aa25	PENDING	PROCESSING	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	ASSIGN	为安装防毒软体	{}	2026-07-29 07:49:48.544407
dec996ff-d10d-4af9-9878-caa02082127c	8b52c741-e068-4393-aa90-798e4324aa25	PROCESSING	PENDING_SIGNOFF	3cd97fb7-2993-410d-9c66-bbfbcd00fba3	PROCESS		{}	2026-07-29 07:54:27.065605
5d706194-8c33-4996-b9a7-62d9c15b3fa9	8b52c741-e068-4393-aa90-798e4324aa25	PENDING_SIGNOFF	CLOSED	3cd97fb7-2993-410d-9c66-bbfbcd00fba3	APPROVE		{}	2026-07-29 07:54:38.461747
\.


--
-- Data for Name: exception_ticket; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.exception_ticket (id, inspection_id, plant_id, title, status, current_assignee_id, created_at, updated_at) FROM stdin;
0f2ead54-cbef-4b0f-a543-89e03d21eb67	f7ab0f88-16c9-44f8-8c75-c9dede3ead6a	11111111-1111-1111-1111-111111111111	未入域	CLOSED	3cd97fb7-2993-410d-9c66-bbfbcd00fba3	\N	2026-07-29 06:53:45.733762
9f06d542-df8f-46cf-9cd0-d30f3609964f	f85c2952-f8c3-484c-80cd-1138d8e250c5	11111111-1111-1111-1111-111111111111	防毒软件异常	PROCESSING	a60e648f-d44a-42b4-9e7d-c43ba5b70fe5	2026-07-29 06:38:02.461337	2026-07-29 06:54:52.401255
8b52c741-e068-4393-aa90-798e4324aa25	e1f6d67a-c5ac-4d78-b2fb-e1efac11b3fe	11111111-1111-1111-1111-111111111111	防毒软件异常 - 未入域	CLOSED	3cd97fb7-2993-410d-9c66-bbfbcd00fba3	2026-07-29 07:48:49.96717	2026-07-29 07:54:38.462415
\.


--
-- Data for Name: inspection; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.inspection (id, serial_no, plant_id, line_id, station_id, ip_address, antivirus_status, domain_status, remark, status, inspector_id, inspect_time, created_at, updated_at) FROM stdin;
3a962dc1-56df-4483-89ed-8e0661c62ed6	INS-20260729-EFD1	11111111-1111-1111-1111-111111111111	33333333-3333-3333-3333-333333333333	66666666-6666-6666-6666-666666666666	192.168.1.100	NORMAL	JOINED	测试	SUBMITTED	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	2026-07-29 04:30:51.471381	2026-07-29 04:30:51.471383	2026-07-29 04:30:51.471383
1785dbb4-0852-4af3-86f1-fd9d88f2e55c	INS-20260729-8A82	11111111-1111-1111-1111-111111111111	44444444-4444-4444-4444-444444444444	88888888-8888-8888-8888-888888888888	10.1.1.1	NORMAL	JOINED	测试	SUBMITTED	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	2026-07-29 04:45:11.351234	2026-07-29 04:45:11.351236	2026-07-29 04:45:11.351237
7079f955-2743-4879-98ff-27009114d601	INS-20260729-1B48	11111111-1111-1111-1111-111111111111	33333333-3333-3333-3333-333333333333	66666666-6666-6666-6666-666666666666	10.1.1.1	NORMAL	JOINED	测试	SUBMITTED	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	2026-07-29 04:51:09.352706	2026-07-29 04:51:09.352707	2026-07-29 04:51:09.352708
805c3eb3-3bb3-4106-b038-b1e23b1904ba	INS-20260729-9D57	11111111-1111-1111-1111-111111111111	33333333-3333-3333-3333-333333333333	66666666-6666-6666-6666-666666666666	10.1.1.2	NORMAL	JOINED	测试3	SUBMITTED	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	2026-07-29 04:59:47.395693	2026-07-29 04:59:47.395696	2026-07-29 04:59:47.395697
cff98a8b-e863-4e29-8735-c0978cfb8098	INS-20260729-7137	11111111-1111-1111-1111-111111111111	44444444-4444-4444-4444-444444444444	88888888-8888-8888-8888-888888888888	10.19.1.1	NORMAL	JOINED	test	SUBMITTED	cfa811de-c2a0-4fe6-9a5c-7ec26af02fb1	2026-07-29 05:43:13.874229	2026-07-29 05:43:13.874231	2026-07-29 05:43:13.874231
f7ab0f88-16c9-44f8-8c75-c9dede3ead6a	INS-20260729-753F	11111111-1111-1111-1111-111111111111	33333333-3333-3333-3333-333333333333	66666666-6666-6666-6666-666666666666	192.168.1.200	NORMAL	NOT_JOINED	测试异常	SUBMITTED	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	2026-07-29 06:23:30.976801	2026-07-29 06:23:30.976804	2026-07-29 06:23:30.976804
f85c2952-f8c3-484c-80cd-1138d8e250c5	INS-20260729-109A	11111111-1111-1111-1111-111111111111	33333333-3333-3333-3333-333333333333	66666666-6666-6666-6666-666666666666	1.1.1.1	ABNORMAL	JOINED		SUBMITTED	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	2026-07-29 06:38:02.454616	2026-07-29 06:38:02.454618	2026-07-29 06:38:02.454619
a5c26c8a-71c3-4e36-ac00-96cbbdf2ea4d	INS-20260729-159A	22222222-2222-2222-2222-222222222222	99999999-9999-9999-9999-999999999999	aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	2.2.2.2	NORMAL	JOINED	测试	SUBMITTED	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	2026-07-29 06:40:30.594053	2026-07-29 06:40:30.594055	2026-07-29 06:40:30.594056
fdc6466d-4ea2-46c1-ac44-b5cf57ba8f4a	INS-20260729-DEC8	11111111-1111-1111-1111-111111111111	44444444-4444-4444-4444-444444444444	88888888-8888-8888-8888-888888888888	1.1.2.1	NOT_INSTALLED	JOINED	测试	SUBMITTED	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	2026-07-29 07:46:49.127208	2026-07-29 07:46:49.127211	2026-07-29 07:46:49.127212
e1f6d67a-c5ac-4d78-b2fb-e1efac11b3fe	INS-20260729-12BA	11111111-1111-1111-1111-111111111111	44444444-4444-4444-4444-444444444444	88888888-8888-8888-8888-888888888888	1.24.5.1	ABNORMAL	NOT_JOINED	测试	SUBMITTED	d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	2026-07-29 07:48:49.96059	2026-07-29 07:48:49.960592	2026-07-29 07:48:49.960593
\.


--
-- Data for Name: inspection_image; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.inspection_image (id, inspection_id, file_name, storage_key, file_size, mime_type, sort_order) FROM stdin;
c230216a-260d-459a-a721-8601eb0b5b27	7079f955-2743-4879-98ff-27009114d601	Fortinet.png	inspection/20260729045102_Fortinet.png	\N	image/jpeg	0
8f53617c-49e3-4939-8973-ab264770dc2f	805c3eb3-3bb3-4106-b038-b1e23b1904ba	Fortinet.png	inspection/20260729045941_Fortinet.png	\N	image/jpeg	0
5adb13cb-1c68-4408-baca-4f32f7d52f36	cff98a8b-e863-4e29-8735-c0978cfb8098	Fortinet.png	inspection/20260729054302_Fortinet.png	\N	image/jpeg	0
76b46ed9-6e0d-4ed3-8c31-034dc21242f7	f7ab0f88-16c9-44f8-8c75-c9dede3ead6a	111.pjp	inspection/20260729062329_111.pjp	\N	image/jpeg	0
63d4c796-3c0d-4f3f-8fdf-f6d1666549c4	f85c2952-f8c3-484c-80cd-1138d8e250c5	111.pjp	inspection/20260729063801_111.pjp	\N	image/jpeg	0
12f5bb64-57f0-4e25-85a9-8c2739e5a8a9	a5c26c8a-71c3-4e36-ac00-96cbbdf2ea4d	Fortinet.png	inspection/20260729064029_Fortinet.png	\N	image/jpeg	0
bedd047b-9ede-42cb-af98-77f8156e68d6	fdc6466d-4ea2-46c1-ac44-b5cf57ba8f4a	111.pjp	inspection/20260729074645_111.pjp	\N	image/jpeg	0
08445534-bd8a-4eb0-8c78-e567836145e7	e1f6d67a-c5ac-4d78-b2fb-e1efac11b3fe	Fortinet.png	inspection/20260729074847_Fortinet.png	\N	image/jpeg	0
\.


--
-- Data for Name: line; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.line (id, plant_id, code, name) FROM stdin;
33333333-3333-3333-3333-333333333333	11111111-1111-1111-1111-111111111111	L1	A线
44444444-4444-4444-4444-444444444444	11111111-1111-1111-1111-111111111111	L2	B线
55555555-5555-5555-5555-555555555555	22222222-2222-2222-2222-222222222222	L3	C线
99999999-9999-9999-9999-999999999999	22222222-2222-2222-2222-222222222222	L3	C线
\.


--
-- Data for Name: plant; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.plant (id, code, name) FROM stdin;
11111111-1111-1111-1111-111111111111	P1	A厂区
22222222-2222-2222-2222-222222222222	P2	B厂区
\.


--
-- Data for Name: role; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.role (id, code, name, description) FROM stdin;
\.


--
-- Data for Name: station; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.station (id, line_id, code, name) FROM stdin;
66666666-6666-6666-6666-666666666666	33333333-3333-3333-3333-333333333333	S1	A站
77777777-7777-7777-7777-777777777777	33333333-3333-3333-3333-333333333333	S2	B站
88888888-8888-8888-8888-888888888888	44444444-4444-4444-4444-444444444444	S3	C站
aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa	99999999-9999-9999-9999-999999999999	S4	D站
bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb	99999999-9999-9999-9999-999999999999	S5	E站
\.


--
-- Data for Name: sys_user; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.sys_user (id, username, password_hash, real_name, mobile, is_active, is_superadmin, created_at, updated_at) FROM stdin;
d3daf193-31a8-4a5e-9a70-cf16c1adf1b9	admin	$2b$12$iwYyTalh9Vv5O8PRnxEGoOBcJy8uQzBnc5Jt5g9Hc/uVvXNEsrWC.	系统管理员	\N	t	t	2026-07-29 02:41:20.847139	2026-07-29 02:41:20.847141
cfa811de-c2a0-4fe6-9a5c-7ec26af02fb1	test2	$2b$12$MgGE5QKQj7Ackil0.zqAuOt8ZCK7vBNHYwZgJ3rDW6TYqwRaPYNj2			f	f	2026-07-29 05:39:46.403585	2026-07-29 06:36:29.102781
3cd97fb7-2993-410d-9c66-bbfbcd00fba3	user1	$2b$12$gmPNQgl/5G4bdoItJ5OWr.QTEVCVT7P7ctH/XamCOUWBVkS7EOpMu			t	f	2026-07-29 06:36:48.594505	2026-07-29 06:36:48.594507
a60e648f-d44a-42b4-9e7d-c43ba5b70fe5	user2	$2b$12$42LzzMom2qeTY3yVN5/cr.Pr6lTQ8sZhCRw54NNGjI9pwXWyz6Uoy			t	f	2026-07-29 06:37:02.111209	2026-07-29 06:37:02.111213
\.


--
-- Data for Name: user_plant; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.user_plant (user_id, plant_id) FROM stdin;
cfa811de-c2a0-4fe6-9a5c-7ec26af02fb1	22222222-2222-2222-2222-222222222222
3cd97fb7-2993-410d-9c66-bbfbcd00fba3	11111111-1111-1111-1111-111111111111
a60e648f-d44a-42b4-9e7d-c43ba5b70fe5	22222222-2222-2222-2222-222222222222
\.


--
-- Data for Name: user_role; Type: TABLE DATA; Schema: public; Owner: inspection_user
--

COPY public.user_role (user_id, role_id) FROM stdin;
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: exception_history exception_history_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.exception_history
    ADD CONSTRAINT exception_history_pkey PRIMARY KEY (id);


--
-- Name: exception_ticket exception_ticket_inspection_id_key; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.exception_ticket
    ADD CONSTRAINT exception_ticket_inspection_id_key UNIQUE (inspection_id);


--
-- Name: exception_ticket exception_ticket_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.exception_ticket
    ADD CONSTRAINT exception_ticket_pkey PRIMARY KEY (id);


--
-- Name: inspection_image inspection_image_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.inspection_image
    ADD CONSTRAINT inspection_image_pkey PRIMARY KEY (id);


--
-- Name: inspection inspection_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.inspection
    ADD CONSTRAINT inspection_pkey PRIMARY KEY (id);


--
-- Name: inspection inspection_serial_no_key; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.inspection
    ADD CONSTRAINT inspection_serial_no_key UNIQUE (serial_no);


--
-- Name: line line_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.line
    ADD CONSTRAINT line_pkey PRIMARY KEY (id);


--
-- Name: plant plant_code_key; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.plant
    ADD CONSTRAINT plant_code_key UNIQUE (code);


--
-- Name: plant plant_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.plant
    ADD CONSTRAINT plant_pkey PRIMARY KEY (id);


--
-- Name: role role_code_key; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.role
    ADD CONSTRAINT role_code_key UNIQUE (code);


--
-- Name: role role_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.role
    ADD CONSTRAINT role_pkey PRIMARY KEY (id);


--
-- Name: station station_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_pkey PRIMARY KEY (id);


--
-- Name: sys_user sys_user_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_pkey PRIMARY KEY (id);


--
-- Name: sys_user sys_user_username_key; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_username_key UNIQUE (username);


--
-- Name: user_plant user_plant_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.user_plant
    ADD CONSTRAINT user_plant_pkey PRIMARY KEY (user_id, plant_id);


--
-- Name: user_role user_role_pkey; Type: CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: exception_history exception_history_operator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.exception_history
    ADD CONSTRAINT exception_history_operator_id_fkey FOREIGN KEY (operator_id) REFERENCES public.sys_user(id);


--
-- Name: exception_history exception_history_ticket_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.exception_history
    ADD CONSTRAINT exception_history_ticket_id_fkey FOREIGN KEY (ticket_id) REFERENCES public.exception_ticket(id);


--
-- Name: exception_ticket exception_ticket_current_assignee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.exception_ticket
    ADD CONSTRAINT exception_ticket_current_assignee_id_fkey FOREIGN KEY (current_assignee_id) REFERENCES public.sys_user(id);


--
-- Name: exception_ticket exception_ticket_inspection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.exception_ticket
    ADD CONSTRAINT exception_ticket_inspection_id_fkey FOREIGN KEY (inspection_id) REFERENCES public.inspection(id);


--
-- Name: exception_ticket exception_ticket_plant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.exception_ticket
    ADD CONSTRAINT exception_ticket_plant_id_fkey FOREIGN KEY (plant_id) REFERENCES public.plant(id);


--
-- Name: inspection_image inspection_image_inspection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.inspection_image
    ADD CONSTRAINT inspection_image_inspection_id_fkey FOREIGN KEY (inspection_id) REFERENCES public.inspection(id);


--
-- Name: inspection inspection_inspector_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.inspection
    ADD CONSTRAINT inspection_inspector_id_fkey FOREIGN KEY (inspector_id) REFERENCES public.sys_user(id);


--
-- Name: inspection inspection_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.inspection
    ADD CONSTRAINT inspection_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.line(id);


--
-- Name: inspection inspection_plant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.inspection
    ADD CONSTRAINT inspection_plant_id_fkey FOREIGN KEY (plant_id) REFERENCES public.plant(id);


--
-- Name: inspection inspection_station_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.inspection
    ADD CONSTRAINT inspection_station_id_fkey FOREIGN KEY (station_id) REFERENCES public.station(id);


--
-- Name: line line_plant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.line
    ADD CONSTRAINT line_plant_id_fkey FOREIGN KEY (plant_id) REFERENCES public.plant(id);


--
-- Name: station station_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.station
    ADD CONSTRAINT station_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.line(id);


--
-- Name: user_plant user_plant_plant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.user_plant
    ADD CONSTRAINT user_plant_plant_id_fkey FOREIGN KEY (plant_id) REFERENCES public.plant(id);


--
-- Name: user_plant user_plant_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.user_plant
    ADD CONSTRAINT user_plant_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.sys_user(id);


--
-- Name: user_role user_role_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.role(id);


--
-- Name: user_role user_role_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: inspection_user
--

ALTER TABLE ONLY public.user_role
    ADD CONSTRAINT user_role_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.sys_user(id);


--
-- PostgreSQL database dump complete
--

\unrestrict CehBmTBKOyjtXchjn1EyzbZXWTq9shd2OjFBQ9Ckn2Py7lkpLN3Tg4DReLqLAkl

