-- ============================================
-- CARGA DE DATOS INICIAL PARA APP DE EVENTOS
-- ============================================

-- 1. USUARIOS (con login social)
INSERT INTO users (name, email, provider, provider_id, role, creator_type)
VALUES 
('Lucas Ramos', 'lucas@example.com', 'google', 'google-uid-123', 'user', NULL),
('Ana Martínez', 'ana@example.com', 'apple', 'apple-uid-456', 'organizer', 'planner'),
('Fundación EcoVida', 'ecovida@example.com', 'google', 'google-uid-789', 'organizer', 'fundraiser');

-- 2. ORGANIZADORES (solo para los usuarios con rol organizer)
INSERT INTO organizers (user_id, bio, logo_url, social_links, verified)
VALUES
((SELECT id FROM users WHERE email='ana@example.com'), 
 'Amante de la fotografía y el arte. Organizo exposiciones culturales.', 
 'https://example.com/logos/ana.png', 
 '{"instagram":"https://instagram.com/anaphoto"}', 
 TRUE),

((SELECT id FROM users WHERE email='ecovida@example.com'), 
 'ONG dedicada a proyectos de reforestación y educación ambiental.', 
 'https://example.com/logos/ecovida.png', 
 '{"facebook":"https://facebook.com/ecovida","website":"https://ecovida.org"}', 
 TRUE);

-- 3. LOCACIONES
INSERT INTO locations (name, latitude, longitude, address)
VALUES
('Parque Central', 9.933, -84.083, 'San José, Costa Rica'),
('Galería Arte Vivo', 9.935, -84.079, 'Av. Central 123, San José');

-- 4. CATEGORÍAS DE EVENTOS
INSERT INTO categories (name, description)
VALUES
('Música', 'Conciertos, shows en vivo, festivales de música'),
('Deportes', 'Carreras, partidos, torneos'),
('Arte y Cultura', 'Exposiciones, teatro, cine'),
('Educación', 'Charlas, talleres, conferencias'),
('Comunidad', 'Eventos sociales y sin fines de lucro');

-- 5. EVENTOS
INSERT INTO events (title, description, location_id, start_time, end_time, is_recurring, recurrence_rule, created_by, status)
VALUES
('Exposición de Fotografía - Naturaleza Urbana', 
 'Una colección de fotos de la ciudad y su relación con la naturaleza.', 
 (SELECT id FROM locations WHERE name='Galería Arte Vivo'), 
 '2025-09-10 17:00:00', '2025-09-10 20:00:00', 
 FALSE, NULL, 
 (SELECT id FROM organizers WHERE bio LIKE '%fotografía%'), 
 'active'),

('Clase de Yoga en el Parque', 
 'Sesión abierta para todo público, nivel principiante.', 
 (SELECT id FROM locations WHERE name='Parque Central'), 
 '2025-09-15 07:00:00', '2025-09-15 08:00:00', 
 TRUE, 'RRULE:FREQ=WEEKLY;BYDAY=MO', 
 (SELECT id FROM organizers WHERE bio LIKE '%fotografía%'), 
 'active'),

('Jornada de Reforestación Comunitaria', 
 'Ven y participa en la siembra de árboles nativos.', 
 (SELECT id FROM locations WHERE name='Parque Central'), 
 '2025-09-20 09:00:00', '2025-09-20 13:00:00', 
 FALSE, NULL, 
 (SELECT id FROM organizers WHERE bio LIKE '%ONG dedicada%'), 
 'active');

-- 6. RELACIÓN EVENTOS - CATEGORÍAS
INSERT INTO event_categories (event_id, category_id)
VALUES
((SELECT id FROM events WHERE title LIKE 'Exposición de Fotografía%'), (SELECT id FROM categories WHERE name='Arte y Cultura')),
((SELECT id FROM events WHERE title LIKE 'Clase de Yoga%'), (SELECT id FROM categories WHERE name='Comunidad')),
((SELECT id FROM events WHERE title LIKE 'Jornada de Reforestación%'), (SELECT id FROM categories WHERE name='Comunidad'));

-- 7. RSVP (usuarios confirmando asistencia)
INSERT INTO rsvp (event_id, user_id, status)
VALUES
((SELECT id FROM events WHERE title LIKE 'Exposición de Fotografía%'), (SELECT id FROM users WHERE email='lucas@example.com'), 'going'),
((SELECT id FROM events WHERE title LIKE 'Clase de Yoga%'), (SELECT id FROM users WHERE email='lucas@example.com'), 'maybe');

-- 8. FAVORITOS
INSERT INTO favorites (user_id, event_id)
VALUES
((SELECT id FROM users WHERE email='lucas@example.com'), (SELECT id FROM events WHERE title LIKE 'Exposición de Fotografía%'));

-- 9. REVIEWS (sobre organizadores)
INSERT INTO reviews (reviewer_id, organizer_id, rating, comment)
VALUES
((SELECT id FROM users WHERE email='lucas@example.com'), 
 (SELECT id FROM organizers WHERE bio LIKE '%fotografía%'), 
 5, 'Excelente evento y organización.');
