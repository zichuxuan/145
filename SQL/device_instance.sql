/*
 Navicat Premium Dump SQL

 Source Server         : 工控机192.168.1.136
 Source Server Type    : MySQL
 Source Server Version : 80045 (8.0.45)
 Source Host           : 192.168.1.136:3306
 Source Schema         : iot_db

 Target Server Type    : MySQL
 Target Server Version : 80045 (8.0.45)
 File Encoding         : 65001

 Date: 27/04/2026 18:47:52
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for device_instance
-- ----------------------------
DROP TABLE IF EXISTS `device_instance`;
CREATE TABLE `device_instance`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `device_model_id` int NULL DEFAULT NULL COMMENT '设备型号id',
  `device_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '设备编号',
  `device_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '设备名称',
  `device_category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '设备类别',
  `production_line` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '所属产线',
  `location` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '所在位置',
  `device_status` tinyint NULL DEFAULT 0 COMMENT '设备状态：0-离线，1-在线，2-运行中，3-故障',
  `device_data` json NULL COMMENT '设备数据(JSON格式)：运行时长、最大容量等',
  `communication_protocol` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '设备通讯协议',
  `is_deleted` tinyint(1) NULL DEFAULT 0 COMMENT '逻辑删除标志：0-未删除，1-已删除',
  `deleted_at` datetime NULL DEFAULT NULL COMMENT '删除时间',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `recent_maintenance_time` datetime NULL DEFAULT NULL COMMENT '最近维护时间',
  `commissioning_time` datetime NULL DEFAULT NULL COMMENT '投运时间',
  `device_image` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '设备图片',
  `enable_or_not` tinyint NULL DEFAULT NULL COMMENT '是否启用:1启用，2禁用',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `device_code`(`device_code` ASC) USING BTREE,
  INDEX `idx_device_model`(`device_model_id` ASC) USING BTREE,
  INDEX `idx_status`(`device_status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '设备实例表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of device_instance
-- ----------------------------
INSERT INTO `device_instance` VALUES (6, NULL, 'DEV7FF027EC', 'SFDS', '输送设备/螺旋输送机', 'SFS', 'SFS', 0, '{\"ip\": \"242\", \"port\": \"22\", \"control_mode\": \"PLC\"}', 'TCP', 0, NULL, '2026-04-22 12:33:26', '2026-04-22 12:37:37', NULL, NULL, NULL, NULL);
INSERT INTO `device_instance` VALUES (7, NULL, 'DEV30ED9824', 'WREW', '输送设备/螺旋输送机', 'QE', 'WW', 0, '{\"ip\": \"1213\", \"port\": \"24\", \"control_mode\": \"PLC\"}', 'TCP', 0, NULL, '2026-04-22 13:00:30', '2026-04-22 13:00:30', NULL, NULL, NULL, NULL);
INSERT INTO `device_instance` VALUES (8, NULL, 'DEV44845C97', 'GTS', '筛选设备/滚筒筛', '', '', 0, '{\"ip\": \"17676\", \"port\": \"34\", \"control_mode\": \"PLC\"}', 'TCP', 0, NULL, '2026-04-23 04:25:43', '2026-04-23 04:25:43', NULL, NULL, NULL, NULL);
INSERT INTO `device_instance` VALUES (9, NULL, 'DEVB7CAC5CA', 'TBJ', '处理设备/破碎机', '', '', 0, '{\"ip\": \"123456\", \"port\": \"1234\", \"control_mode\": \"PLC\"}', 'TCP', 0, '2026-04-23 04:30:04', '2026-04-23 04:29:49', '2026-04-23 04:30:26', NULL, NULL, NULL, NULL);

SET FOREIGN_KEY_CHECKS = 1;
