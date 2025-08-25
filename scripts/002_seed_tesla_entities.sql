-- Seed Tesla and competitor entities for initial testing

-- Tesla Products
INSERT INTO entities (name, type, manufacturer, model, version) VALUES
('Tesla Solar Panels', 'pv', 'Tesla', 'Solar Panels', '2024'),
('Tesla Solar Roof', 'pv', 'Tesla', 'Solar Roof', 'V3'),
('Tesla Powerwall 3', 'battery', 'Tesla', 'Powerwall', '3'),
('Tesla Powerwall 2', 'battery', 'Tesla', 'Powerwall', '2'),
('Tesla Megapack', 'battery', 'Tesla', 'Megapack', '2XL')
ON CONFLICT (name, manufacturer, model, version) DO NOTHING;

-- Competitor Products
INSERT INTO entities (name, type, manufacturer, model, version) VALUES
('Enphase IQ Battery 5P', 'battery', 'Enphase', 'IQ Battery', '5P'),
('LG Chem RESU Prime', 'battery', 'LG Chem', 'RESU Prime', '16H'),
('SunPower Maxeon 6', 'pv', 'SunPower', 'Maxeon', '6'),
('Canadian Solar HiKu7', 'pv', 'Canadian Solar', 'HiKu7', 'Mono'),
('Fluence Gridstack Pro', 'battery', 'Fluence', 'Gridstack Pro', '2.0')
ON CONFLICT (name, manufacturer, model, version) DO NOTHING;

-- Create a default scenario for testing
INSERT INTO scenarios (name, use_case, region, load_profile, financing, incentives) VALUES
('Texas Residential', 'residential', 'TX', 
 '{"daily_kwh": 30, "peak_kw": 5, "profile": "residential"}',
 '{"loan_rate": 0.05, "term_years": 25, "down_payment": 0.2}',
 '{"federal_itc": 0.3, "state_rebate": 1000}'
)
ON CONFLICT DO NOTHING;
