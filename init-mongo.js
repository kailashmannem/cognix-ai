// MongoDB initialization script
db = db.getSiblingDB('cognix_platform');

// Create collections with indexes
db.createCollection('users');
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "created_at": 1 });

// Create a default admin user (optional)
// db.users.insertOne({
//   email: "admin@cognix.ai",
//   password_hash: "$2b$12$example_hash",
//   api_keys: {},
//   preferred_llm_provider: "openai",
//   created_at: new Date(),
//   updated_at: new Date()
// });

print('Database initialized successfully');