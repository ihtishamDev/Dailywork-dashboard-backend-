use dailytask;

CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    priority VARCHAR(50),
    work_needed TEXT,
    phone_number VARCHAR(20),
    email VARCHAR(100),
    notes TEXT,
    status VARCHAR(50)
);