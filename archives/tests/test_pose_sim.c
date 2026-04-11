/**
 * CyberWand - 模拟姿态识别单元测试
 * 使用模拟的四元数数据进行测试
 */

#include <stdio.h>
#include <assert.h>
#include <math.h>
#include "pose_model.h"
#include "mpu6050_sim.h"

// 测试统计
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) void name(void)
#define RUN_TEST(name) do { \
    printf("\n[TEST] Running %s...\n", #name); \
    tests_run++; \
    name(); \
    printf("[TEST] ✓ %s PASSED\n", #name); \
    tests_passed++; \
} while(0)

#define ASSERT_EQ(expected, actual, msg) do { \
    if ((expected) != (actual)) { \
        printf("[FAIL] %s: Expected %d, got %d - %s\n", #name, (expected), (actual), (msg)); \
        tests_failed++; \
        return; \
    } \
} while(0)

/**
 * 测试 1: 空闲姿态检测
 */
TEST(test_pose_idle)
{
    mpu6050_sim_action_sequence(ACTION_IDLE);
    
    imu_data_t imu;
    mpu6050_sim_read(&imu);
    
    pose_type_t pose = pose_recognize(&imu, NULL);
    ASSERT_EQ(POSE_IDLE, pose, "Should detect IDLE pose");
}

/**
 * 测试 2: 左旋转检测
 */
TEST(test_pose_rotate_left)
{
    mpu6050_sim_action_sequence(ACTION_ROTATE_LEFT);
    
    imu_data_t imu;
    mpu6050_sim_read(&imu);
    
    pose_type_t pose = pose_recognize(&imu, NULL);
    ASSERT_EQ(POSE_ROTATE_LEFT, pose, "Should detect ROTATE_LEFT pose");
}

/**
 * 测试 3: 右旋转检测
 */
TEST(test_pose_rotate_right)
{
    mpu6050_sim_action_sequence(ACTION_ROTATE_RIGHT);
    
    imu_data_t imu;
    mpu6050_sim_read(&imu);
    
    pose_type_t pose = pose_recognize(&imu, NULL);
    ASSERT_EQ(POSE_ROTATE_RIGHT, pose, "Should detect ROTATE_RIGHT pose");
}

/**
 * 测试 4: V 形上倾斜检测
 */
TEST(test_pose_v_shape_up)
{
    mpu6050_sim_action_sequence(ACTION_V_SHAPE_UP);
    
    imu_data_t imu;
    mpu6050_sim_read(&imu);
    
    pose_type_t pose = pose_recognize(&imu, NULL);
    ASSERT_EQ(POSE_TILT_UP, pose, "Should detect TILT_UP pose");
}

/**
 * 测试 5: V 形下倾斜检测
 */
TEST(test_pose_v_shape_down)
{
    mpu6050_sim_action_sequence(ACTION_V_SHAPE_DOWN);
    
    imu_data_t imu;
    mpu6050_sim_read(&imu);
    
    pose_type_t pose = pose_recognize(&imu, NULL);
    ASSERT_EQ(POSE_TILT_DOWN, pose, "Should detect TILT_DOWN pose");
}

/**
 * 测试 6: 连续动作序列检测
 */
TEST(test_continuous_action_sequence)
{
    // 测试动作序列：空闲 → 左转 → 右转 → 空闲
    action_sequence_t sequence[] = {
        ACTION_IDLE,
        ACTION_ROTATE_LEFT,
        ACTION_ROTATE_RIGHT,
        ACTION_IDLE
    };
    
    pose_type_t expected_poses[] = {
        POSE_IDLE,
        POSE_ROTATE_LEFT,
        POSE_ROTATE_RIGHT,
        POSE_IDLE
    };
    
    for (int i = 0; i < 4; i++) {
        mpu6050_sim_action_sequence(sequence[i]);
        
        imu_data_t imu;
        mpu6050_sim_read(&imu);
        
        pose_type_t pose = pose_recognize(&imu, NULL);
        ASSERT_EQ(expected_poses[i], pose, 
                  "Should detect correct pose in sequence");
    }
}

/**
 * 测试 7: 四元数生成验证
 */
TEST(test_quaternion_generation)
{
    // 测试转圈四元数（90 度）
    quaternion_t q_rot = generate_rotation_quaternion(90);
    assert(fabs(q_rot.w - cosf(M_PI/4)) < 0.01);
    assert(fabs(q_rot.z - sinf(M_PI/4)) < 0.01);
    printf("  Quaternion (90°): w=%.3f, z=%.3f\n", q_rot.w, q_rot.z);
    
    // 测试 V 形四元数（45 度）
    quaternion_t q_v = generate_v_shape_quaternion(45);
    assert(fabs(q_v.w - cosf(M_PI/8)) < 0.01);
    assert(fabs(q_v.x - sinf(M_PI/8)) < 0.01);
    printf("  Quaternion (45°): w=%.3f, x=%.3f\n", q_v.w, q_v.x);
}

/**
 * 测试 8: 四元数到传感器数据转换
 */
TEST(test_quaternion_to_sensor)
{
    quaternion_t test_q = {0.924, 0, 0, 0.383};  // 45 度旋转
    
    int16_t ax, ay, az;
    quaternion_to_accel(&test_q, &ax, &ay, &az);
    
    printf("  Acceleration: ax=%d, ay=%d, az=%d\n", ax, ay, az);
    
    // 验证 Z 轴加速度接近 1g（静止时）
    assert(az > 10000 && az < 20000);
}

// ================= 主测试函数 =================

int main(void)
{
    printf("========================================\n");
    printf("  CyberWand Pose Recognition Tests\n");
    printf("  (Simulated MPU6050 with Quaternions)\n");
    printf("========================================\n\n");
    
    // 初始化模拟传感器
    mpu6050_sim_init();
    
    // 运行所有测试
    RUN_TEST(test_quaternion_generation);
    RUN_TEST(test_quaternion_to_sensor);
    RUN_TEST(test_pose_idle);
    RUN_TEST(test_pose_rotate_left);
    RUN_TEST(test_pose_rotate_right);
    RUN_TEST(test_pose_v_shape_up);
    RUN_TEST(test_pose_v_shape_down);
    RUN_TEST(test_continuous_action_sequence);
    
    // 统计结果
    printf("\n========================================\n");
    printf("  Test Results\n");
    printf("========================================\n");
    printf("  Total:   %d\n", tests_run);
    printf("  Passed:  %d\n", tests_passed);
    printf("  Failed:  %d\n", tests_failed);
    printf("========================================\n");
    
    if (tests_failed == 0) {
        printf("\n✅ All tests PASSED!\n");
        return 0;
    } else {
        printf("\n❌ Some tests FAILED!\n");
        return 1;
    }
}
