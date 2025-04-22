BEGIN;
CREATE TABLE IF NOT EXISTS staff (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS staff_skills (
    skill_id UUID REFERENCES skill(id),
    staff_id UUID REFERENCES staff(id),
    PRIMARY KEY (skill_id, staff_id)
);
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_tags (
    id UUID PRIMARY KEY,
    name TEXT
);
CREATE TABLE IF NOT EXISTS activity_tag_assocs (
    tag_id UUID REFERENCES activity_tags(id) ON DELETE CASCADE,
    activity_id UUID REFERENCES activities(id) ON DELETE CASCADE,
    PRIMARY KEY (tag_id, activity_id)
);
CREATE TABLE IF NOT EXISTS assignment_tags (
    id UUID PRIMARY KEY,
    name TEXT
);
CREATE TABLE IF NOT EXISTS assignment_tag_assocs (
    tag_id UUID REFERENCES assignment_tags(id) ON DELETE CASCADE,
    activity_id UUID,
    staff_id UUID,
    PRIMARY KEY (tag_id, activity_id, staff_id),
    FOREIGN KEY (activity_id, staff_id) REFERENCES staff_assignment(activity_id, staff_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS timeslots (
    activity_id UUID REFERENCES activities(id),
    start TIMESTAMP,
    finish TIMESTAMP,
    PRIMARY KEY (activity_id, start, finish)
);
CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY,
    type TEXT,
    template_id UUID REFERENCES activities(id),
    name TEXT,
    location_id UUID REFERENCES locations(id),
    recurrence_rules TEXTJSON,
    requirements TEXTJSON,
    activity_start TIMESTAMP,
    activity_finish TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requirement_skills (
    requirement_id INTEGER REFERENCES requirements(id) ON DELETE CASCADE,
    skill_id UUID REFERENCES skill(id) ON DELETE CASCADE,
    PRIMARY KEY (requirement_id, skill_id)
);

CREATE TABLE IF NOT EXISTS staff_assignments (
    activity_id UUID REFERENCES activities(id),
    staff_id UUID REFERENCES staff(id),
    attendance INTEGER DEFAULT 100,
    start_time TIMESTAMP,
    finish_time TIMESTAMP,
    PRIMARY KEY (activity_id, staff_id)
);
CREATE TABLE IF NOT EXISTS personal_patterns (
    id UUID PRIMARY KEY,
    staff UUID,
    ruleset TEXT,
    name TEXT
);
CREATE TABLE IF NOT EXISTS personal_pattern_entry (
    id SERIAL PRIMARY KEY,
    dateoffset INTEGER,
    activity_tags TEXT,
    template_id TEXT REFERENCES personal_patterns(id),
    pattern_id INTEGER REFERENCES personal_patterns(id)
);
CREATE TABLE IF NOT EXISTS personal_pattern_activity_tag_assocs (
    tag_id UUID REFERENCES activity_tags(id) ON DELETE CASCADE,
    pattern_id UUID REFERENCES personal_pattern_entry(id) ON DELETE CASCADE,
    PRIMARY KEY (tag_id, pattern_id)
);
PRAGMA foreign_keys = ON;
COMMIT;
