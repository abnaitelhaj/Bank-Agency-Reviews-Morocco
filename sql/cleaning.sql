-- Fix common UTF-8 mojibake in staging bank and location names

UPDATE bank_reviews_staging
SET bank_name = 'Crédit Agricole'
WHERE bank_name ILIKE '%cr%dit agricole%'
   OR bank_name = 'credit agricole';

UPDATE bank_reviews_staging
SET bank_name = 'Crédit du Maroc'
WHERE bank_name ILIKE '%cr%dit du maroc%'
   OR bank_name = 'CREDIT DU MAROC';

UPDATE bank_reviews_staging
SET bank_name = 'Société Générale'
WHERE bank_name ILIKE '%soci%t% g%n%rale%'
   OR bank_name = 'SOCIETE GENERALE';

UPDATE bank_reviews_staging
SET
    address = REPLACE(REPLACE(address, 'Ã©', 'é'), 'Ã¨', 'è'),
    branch_name = REPLACE(REPLACE(branch_name, 'Ã©', 'é'), 'Ã¨', 'è'),
    region = REPLACE(REPLACE(region, 'Ã©', 'é'), 'Ã¨', 'è')
WHERE address LIKE '%Ã©%'
   OR address LIKE '%Ã¨%'
   OR branch_name LIKE '%Ã©%'
   OR branch_name LIKE '%Ã¨%'
   OR region LIKE '%Ã©%'
   OR region LIKE '%Ã¨%';
