-- 创建 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 预设角色：厂区Member（普通成员）和厂区Leader（管理者）
INSERT INTO role (id, code, name, description) VALUES
    (uuid_generate_v4(), 'PLANT_MEMBER', '厂区Member', '厂区普通成员，可进行巡检录入和查询'),
    (uuid_generate_v4(), 'PLANT_LEADER', '厂区Leader', '厂区管理者，可进行巡检录入、查询及异常签核')
ON CONFLICT (code) DO NOTHING;