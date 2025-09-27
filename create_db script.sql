-- ============================================
-- CREACIÓN DE TABLAS PARA APP DE EVENTOS
-- ============================================

-- 1. USERS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    provider TEXT CHECK (provider IN ('google', 'apple')) NOT NULL,
    provider_id TEXT NOT NULL,
    role TEXT CHECK (role IN ('user', 'organizer', 'admin')) DEFAULT 'user',
    creator_type TEXT CHECK (creator_type IN ('comercio', 'planner', 'fundraiser')) NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. ORGANIZERS (1:1 con users)
CREATE TABLE organizers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    logo_url TEXT,
    social_links JSONB,
    verified BOOLEAN DEFAULT FALSE
);

-- 3. LOCATIONS
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name TEXT,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    address TEXT
);

-- 4. EVENTS
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    location_id INT REFERENCES locations(id) ON DELETE SET NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_rule TEXT,
    created_by UUID REFERENCES organizers(id) ON DELETE CASCADE,
    status TEXT CHECK (status IN ('active', 'cancelled', 'past')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. CATEGORIES
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

-- 6. EVENT_CATEGORIES (relación N:N)
CREATE TABLE event_categories (
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    category_id INT REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, category_id)
);

-- 7. RSVP (ASISTENCIAS)
CREATE TABLE rsvp (
    id SERIAL PRIMARY KEY,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status TEXT CHECK (status IN ('going', 'maybe')) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (event_id, user_id) -- evita duplicados
);

-- 8. REVIEWS (SOBRE ORGANIZADORES)
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    reviewer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organizer_id UUID REFERENCES organizers(id) ON DELETE CASCADE,
    rating SMALLINT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 9. FAVORITES
CREATE TABLE favorites (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE (user_id, event_id) -- evita duplicados
);

-- 10. NOTIFICATIONS
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    type TEXT CHECK (type IN ('event_update', 'reminder', 'system')),
    status TEXT CHECK (status IN ('unread', 'read')) DEFAULT 'unread',
    created_at TIMESTAMP DEFAULT NOW()
);
