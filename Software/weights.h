#include "nnom.h"

/* Weights, bias and Q format */
#define TENSOR_CONV1D_KERNEL_0 {-10, -77, 61, -14, -41, -51, 45, -76, 63, 45, -39, 53, -1, 34, 55, 3, -52, 36, -10, 33, 1, 31, -46, -21, -16, 59, -42, 35, 14, 68, -72, -34, -24, -44, 12, 50, 61, 1, -64, -5, -1, -32, -24, -64, -1, 19, 32, -16, 9, -5, 36, 18, 25, -18, 28, -2, -31, 21, -70, 30, 29, 14, -49, 56, 24, -40, -43, 57, 5, -20, -63, 4, -30, 76, -31, 19, 73, -38, 55, 75, 17, 32, -11, 52, 48, -22, -35, 7, 45, 44, 2, 7, 56, 50, -36, 51, 13, 53, -19, 55, -1, 10, 56, 75, -8, 14, 42, -52, 36, 15, -1, -7, 43, 62, -12, 49, 36, 7, -59, 49, 11, 60, 23, -71, -54, 60, -3, 62, -32, 39, 46, -20, -28, 66, 27, -2, -62, 66, 39, 35, 66, -41, 45, 8, -18, 27, -29, 41, -27, -21, -8, -8, -40, -43, -57, 9, -53, -22, 40, 38, 37, 6, 35, -25, 11, 6, -33, -24, 41, 16, 42, -21, -18, -8, 47, 67, -59, -17, -3, -29, 15, -5, 45, -30, 24, 27, 22, 64, -35, 27, -25, -26, 53, 68, 48, 1, 64, 16, 36, -55, 58, 24, -6, 24, -45, -68, -33, -60, 46, -50, -34, -34, 56, -19, 2, -53, -5, -42, 12, -55, -29, -19, 7, -18, 9, -50, 32, -37, -34, -45, 27, -49, -21, 42, -9, 43, -38, 29, -52, -41, 56, 42, -19, -6, -30, -28, 61, -12, 6, -33, -10, -24, 40, -63, 33, 66, -42, 43, 49, 18, -53, -6, -49, 2, -19, 30, -29, 25, -63, -1, -32, 27, 27, 32, -59, 45, 31, 31, -32, 23, 2, -22, -55, -43, -5, 14, 34, 24, -17, 58, -13, 42, -42, 33, -40, -28, -17, 50, -59, 14, -28, 67, 55, 13, -30, -11, 58, -60, 31, -25, 53, -7, -48, 14, 67, -48, -14, 63, 59, -71, -26, 28, 54, 27, -52, -9, 45, -24, -37, 2, 40, 23, -27, -60, 31, -33, 27, 74, 54, 41, -18, -28, -27, 24, 33, 68, 66, -29, -1, -6, 26, 9, -21, 17, -45, 38, -33, 33, -24, -46, 41, -52, -2, -1, 43, -31, -52, -14, 60, 11, -60, -53, 1, -8, -3, 52, 6, 6, 10, 1, -55, 36, 41, 68, 0, -31, 14, -43, 38, 43, 30, 2, 2, 24, -54, -3, -12, -1, 40, 36, -63, -42, -47, 17, 10, 40, 38, -49, 9, 44, -64, 65, 51, -25, -37, 11, 44, -9, 29, 33, -52, -29, -29, -21, 43, -53, 19, 67, -29, -28, 32, -38, 30, 11, -6, -49, 30, -32, -1, 3, -52, 57, -45, 27, -5, 15, 15, 39, -59, 37, 6, 29, -7, 54, 5, 32, -26, 7, 42, 16, 3, 9, -31, 12, -5, -40, 14, -59, 13, -67, -46, -34, 4, -16, 49, -71, 29, 38, 1, 17, -39, -4, 55, 51, 4, -37, -38, -6, -56, 57, 59, -38, -3, 67, 11, -32, 44, 61, -2, 12, -48, 27, 61, 56, -29, -41, 30, 14, 1, -39, -47, -28, -20, -19, -44, -50, 4, 26, -44, -21, -46, -15, 3, 29, -60, -13, -46, -30, -41, 9, -23, -34, -21, -40, -54, -41, 38, -15, 43, 43}

#define TENSOR_CONV1D_KERNEL_0_DEC_BITS {8}

#define TENSOR_CONV1D_BIAS_0 {31, 45, 21, 10, 32, 65, 14, 10, -33, -19, -4, 15, -18, 15, -6, 34, 9, 60, 57, -42, 51, -12, -29, 67, 15, -9, 37, -1, -58, 2}

#define TENSOR_CONV1D_BIAS_0_DEC_BITS {10}

#define CONV1D_BIAS_LSHIFT {2}

#define CONV1D_OUTPUT_RSHIFT {9}

#define TENSOR_CONV1D_1_KERNEL_0 {41, -2, -30, 15, 19, 14, -52, 4, -30, -6, 26, -28, 4, -10, 19, 51, -22, 52, 1, -48, 8, -16, -38, 35, 15, 65, 36, -28, -59, 8, 29, -35, -23, 21, -18, 48, 33, -6, -59, -15, -23, -3, -34, 43, 18, -29, -32, 3, 53, -41, 43, -38, -4, -10, 37, -14, 52, -3, -48, -14, 22, -56, 2, 32, -41, 33, -36, -12, -30, -50, -31, 40, 15, -27, 14, 36, -12, 57, -35, 2, 25, -11, -40, -33, -38, -18, -1, -14, -1, -45, 38, 42, 46, 40, -14, 35, 37, -10, 41, -26, 6, 35, -6, -24, -8, -13, 29, 51, -31, -18, -13, -50, -25, -50, -31, -15, 16, 0, -50, -18, -11, 23, 21, 28, -33, -38, 40, 16, -8, 13, 8, -47, 12, -1, -45, -57, -19, 55, 10, -58, -39, -26, -33, 23, 38, -35, 50, -24, 12, 57, 0, 40, 22, 2, -24, 37, -38, 48, -40, 0, 49, -44, -21, 23, 9, 33, -17, 22, -20, 14, -39, 32, -39, -41, -22, -56, -34, 31, 25, 5, -26, -40, -49, -48, 52, 63, -28, -27, -33, -36, 26, -39, -40, 42, 41, -23, -17, 36, 11, 13, 4, -31, 18, 14, 51, 36, -25, -9, -17, 27, 31, 7, 29, 13, 9, -12, 5, 68, -11, 13, 3, 15, 47, 2, 11, 8, 23, 9, 36, -42, 3, 19, 30, 18, 24, 19, 35, -5, 38, -8, -40, 33, 54, -6, 44, 38, -1, 64, 2, -19, 69, -51, -45, -51, -8, -45, -37, 43, 0, -26, -10, 27, -43, 65, -68, -28, 26, -7, -7, -25, 6, -63, 40, 19, -38, 14, 7, -37, -17, 7, 59, -40, -9, 17, -48, -32, 8, 41, -38, 16, -33, -47, -25, 19, 22, -22, 8, -59, 1, -27, -52, -50, -52, -24, 23, 6, -21, 14, -12, -5, 14, 45, -36, -11, -49, 33, -55, -56, 9, -38, -1, 22, -52, -28, 15, -28, -8, -1, -22, -4, 46, -20, 32, -19, -6, 32, -10, -37, -44, 42, -2, -32, -49, -17, 40, -11, -57, -49, -38, -24, -12, -53, -10, 26, -14, -18, -12, 0, 35, -42, 51, 25, -25, -14, -14, -9, 34, -25, 20, 10, -14, -25, 43, -14, -36, -25, -5, -25, -31, -25, -36, 5, 28, -7, 12, 15, -16, -51, -31, -18, -47, 35, -17, 35, -52, -10, -48, 14, 7, -7, -18, 52, -30, 0, 19, 39, -12, 48, 0, -50, -21, -6, 43, 53, 4, 20, 25, 12, -27, -17, 49, 62, -41, 6, 36, 2, 10, 4, 46, 41, -40, -38, 3, -5, -13, 52, 15, 15, 33, 54, -20, 49, 4, -22, -3, -4, 21, -24, -4, -40, -41, -14, -50, -8, -24, 1, -40, -65, -24, 18, -55, 13, -16, -36, 44, 23, 4, -50, -20, 20, -45, 32, 46, -17, 25, -1, 8, -27, 20, -9, 39, -28, -29, -4, -48, -46, 20, 6, -4, 39, 28, -44, -1, 19, 36, 16, -12, -65, 18, -39, 48, -20, -50, -43, 35, 32, -2, -63, -4, -22, 22, -23, -43, 28, -30, -51, -50, 11, -10, 14, 27, -21, -43, 30, -34, -7, 27, -55, -34, -50, -38, -65, -25, -13, -22, -1, -46, 27, 47, 45, 33, 28, 39, 3, -20, 5, 11, -43, 24, 38, 25, 27, 33, 19, 39, 28, 31, 25, -14, -25, -1, 24, -54, 15, 36, -44, -44, 25, -16, -12, -18, 25, 42, 39, -41, 33, -28, -54, 37, 52, -11, 10, -40, -31, -23, 45, 9, 46, 47, -32, -23, 29, -11, 8, 48, -19, 45, -6, -41, 11, -3, -34, -43, 23, -10, -8, -23, 38, 36, 2, -19, 39, 44, 55, 42, 52, 14, -51, 14, -48, 29, -52, 21, -19, -38, 31, -34, -12, 34, -7, 2, -20, 31, 8, -21, 50, -24, 17, 15, 56, -31, -43, 53, 19, 19, -45, 6, -2, -17, 47, -8, -19, -13, -10, -39, 19, 6, -32, -16, -17, -42, -42, -26, -23, 28, -49, 52, 15, 19, -5, -17, 36, 36, 4, -2, -30, 40, -23, -41, 13, 29, 38, 31, -59, -11, -45, -9, 0, 16, 19, 2, 17, -7, 17, -22, -5, -18, 2, -10, -52, 2, 27, 51, 47, -21, 34, -41, 55, 0, 12, -8, 38, -29, 22, 9, 45, 52, -51, 11, -49, -54, -32, -45, 16, 56, 55, -43, 21, 22, 20, -42, -58, -25, -33, 60, -3, -34, -44, 45, -11, -22, 64, -30, 30, 56, 28, -54, -17, -51, -31, -40, 47, -56, 10, 26, 2, -18, -49, 54, 35, -14, 35, -26, -12, 12, -22, -15, 33, -15, -10, 36, 58, -9, -5, 45, 36, 31, 0, -27, -33, -11, 44, 40, -11, 0, 16, -3, -28, 34, 42, 15, -12, -35, 27, -23, -41, -41, -14, -15, 3, -7, 18, -28, -68, 43, 43, 36, 6, 6, 11, -26, 13, -41, -48, 41, 39, -12, 68, -48, -34, 12, -8, -15, -5, -31, 48, 14, -20, 33, -23, -61, 31, -30, 34, -11, 50, -24, 25, -18, 57, -34, 11, 0, -50, 7, -18, -20, 72, -8, -20, 0, 46, 6, -29, -44, 42, 44, -8, 29, 22, 13, -26, 14, -25, -14, 29, -44, 7, -41, -2, 11, 42, 42, -69, 14, 49, 21, 23, 39, -38, -16, 2, 3, 23, -29, -26, -55, -40, 48, 18, -46, -41, -19, 54, -25, -18, 33, -35, -19, -17, 45, -61, -10, 35, 28, 25, 2, -62, -5, -22, -1, 33, -44, 25, -7, -19, 6, 5, 7, 40, -16, -18, -37, 1, -15, -8, 28, -46, -26, -44, -39, -18, 24, -3, -12, 31, -37, 0, -36, 34, 1, 43, -9, 1, 5, -44, -8, 16, -16, -59, 33, -41, -30, 19, -15, -53, 64, -43, 12, -13, 19, 42, 47, 20, -43, -56, -33, -53, 38, -17, 13, 2, 36, -11, 21, -7, -50, 40, -5, 25, 5, 7, 51, -16, -37, -10, 14, -22, -40, 41, 33, -43, 30, -58, -26, 26, -17, -47, 22, -44, -54, 40, 18, -34, -40, -53, -31, 20, -28, -47, 2, 10, 18, 6, -63, 46, 9, 9, -2, -32, -54, 24, 28, -53, -6, -20, -11, 32, -41, -58, 22, 15, 30, 6, 42, 39, -34, -32, -18, 48, -23, 31, 38, -18, 35, 46, 17, 23, -18, -30, -36, -36, 57, -21, 28, 23, 6, -29, 1, -27, -27, 17, 30, 44, 9, -28, -22, 3, 42, -21, -14, 38, 23, 26, 43, 30, -31, 18, -10, 31, -46, -10, -14, -12, 42, 22, -25, -7, -2, 20, 17, -37, -33, 2, 48, 44, -27, -15, 15, 3, 34, -17, 57, -34, 3, 46, -38, 4, -1, 42, -50, 50, -27, 44, -51, -4, -33, 38, -16, 18, -39, 17, 13, 22, 4, 17, 36, -61, -34, 48, 1, -50, -38, 34, 21, 25, -22, 19, -32, 39, -15, 57, 49, 68, 3, 15, -37, 35, -7, 49, 33, -41, 3, 28, 51, 26, 45, -32, 17, 37, 7, -24, 42, 43, 50, -45, 36, -5, 44, 21, 31, -27, 42, -1, -8, -48, -52, -31, 42, -41, -2, -9, 20, -2, 43, -19, 29, 22, -29, -21, -8, -48, -56, 18, 36, 41, 70, -18, -49, -6, 12, -54, 34, -36, -59, -54, -36, -27, -30, -10, 13, 37, 27, -24, 17, -21, -14, -44, -18, 7, 34, 28, -6, -38, -25, -2, -23, -32, -15, 6, -25, -39, 40, 14, -39, 12, 23, 8, 29, 35, -9, -17, 0, -39, 31, -15, -44, 41, -10, 6, -13, 47, 50, 24, -1, 0, -9, 6, 18, 22, -52, -29, 19, -13, 43, -31, -48, -34, 16, 46, -48, -12, 2, -11, -64, 12, 0, 49, -46, 3, 7, 5, 21, -23, -57, -30, 20, -23, 43, -19, -41, 47, -14, -42, -3, 49, -49, -30, 58, -45, 35, -24, -54, 11, 3, -20, 31, 12, 37, -12, 43, -54, 56, 1, 25, 3, 54, 40, 10, 63, -25, -23, 13, 5, 45, -16, -34, 20, 51, -8, -58, 19, 1, -17, -36, 6, -36, 22, -41, -16, 63, -17, -8, 37, 19, -20, 30, 21, 58, 54}

#define TENSOR_CONV1D_1_KERNEL_0_DEC_BITS {8}

#define TENSOR_CONV1D_1_BIAS_0 {111, -28, 16, 13, -38, -58, 86, -28, -36, 109, 13, -18, -6, -14, -15}

#define TENSOR_CONV1D_1_BIAS_0_DEC_BITS {11}

#define CONV1D_1_BIAS_LSHIFT {0}

#define CONV1D_1_OUTPUT_RSHIFT {8}

#define TENSOR_DENSE_KERNEL_0 {0, -28, -19, 15, 12, 9, -23, -13, -46, -40, 15, 21, -31, -19, 18, 43, -38, 29, -4, 39, -28, 16, -22, -18, 47, 27, -32, -34, -13, 2, 9, 19, -1, 35, -30, 9, 46, 5, -44, 50, 11, -43, -24, -41, 34, -55, -37, 7, 15, -26, 41, 28, 7, 5, -18, 41, -31, 22, 0, -25, -44, 19, -29, 11, -16, 0, -27, 26, -29, 13, -15, 35, 16, 29, -38, 12, -22, -19, 11, 26, 18, -29, -9, -7, 31, -5, 23, 25, -17, -25, -28, -31, -10, 15, 5, 27, 11, 22, 35, -15, -40, 9, 22, -11, -26, 0, 5, 38, 19, 33, 3, 39, 4, 12, -18, -6, -22, 32, 19, -24, 26, 29, -10, 17, 15, 10, -19, -38, 15, 3, 10, 5, -22, 2, 27, -27, 9, 39, -2, 31, 42, -32, 23, 23, -7, -24, -18, 5, 3, 7, -12, 35, 20, 35, 17, 17, -37, -25, 8, 6, -31, 33, -10, -50, -23, -15, 27, 37, 48, -13, 33, 9, 5, 18, -18, 33, -12, -40, 28, 22, -10, 33, -10, 14, -44, 43, -22, 24, -50, -6, -6, -22, 22, -11, 23, -14, 11, 11, 47, 17, -40, 17, -25, -11, 21, -11, 2, 21, -4, 5, -16, 0, -7, 22, -1, -34, -27, 34, 10, 9, 36, -12, 19, 0, 30, 30, 7, -12, -10, 17, 14, 5, 12, -32, 30, 15, 30, 44, 21, -6, 10, -4, -16, -20, 9, 3, 11, -55, 26, 23, 0, 21, -25, -1, 31, 26, 22, -22, -8, -38, -39, 12, -28, 52, -17, -34, -10, 5, 31, 27, -35, -1, -8, 22, 32, 14, 9, 24, -8, 11, 36, 10, 22, 1, 1, 27, -9, 31, 10, -9, 18, -17, 19, 7, -12, -38, -8, -44, -10, -17, 4, -22, -44, -18, 15, 24, -22, -34, -22, -45, 12, 22, 33, -1, 13, 29, -46, 3, -9, 39, 11, 30, 17, 28, 38, 22, -2, 8, -45, 10, -33, 37, 16, 41, 22, 14, 15, -35, 19, 17, -9, -48, -27, -30, 35, 1, -11, -7, -26, 38, 24, -15, 1, -21, 12, -19, -26, 2, 1, -5, 3, 17, 26, 35, 8, -42, -25, -23, -10, -16, -15, 28, 0, -8, -18, -21, -25, -38, 18, -4, -31, 13, -3, 3, 23, -32, -17, 30, -2, -12, 22, -33, -21, 25, -7, -54, -29, 13, 4, 9, -11, 7, -5, -16, -2, -4, -19, 29, 15, -11, 11, -1, 12, 5, -27, -12, 13, 19, -11, 28, 11, 5, -12, -48, 32, 16, 46, -15, 11, 28, -31, 33, 24, -15, -38, -12, 19, -12, 8, -23, 3, 23, -32, 37, 0, -30, 12, -12, 26, -20, 22, -67, -27, -6, 44, 29, 5, -41, 27, 14, -30, 27, 18, 18, -16, 19, -19, -29, 39, 9, -40, -9, -40, 17, 34, -17, 35, 46, 25, -30, 13, 33, 8, 9, 23, -48, 6, 9, -6, 11, -34, -15, -7, 11, 3, -30, -31, 44, -18, -2, 24, -8, 23, 9, -32, -1, 18, 10, 48, 23, 31, -31, 22, 27, -5, -1, -5, -16, -23, -5, -13, 5, 36, 16, -25, -2, 17, -11, 7, -36, 18, -11, 43, 14, 32, -31, 16, -9, -39, -28, -8, 23, -6, -49, 34, -1, 35, -20, -21, -5, -27, 8, 36, -34, -13, 26, -46, 39, -16, -8, -18, 37, 35, 24, 32, 15, 17, -6, 13, -28, -30, 26, -18, 43, -20, -2, 13, 8, 41, -49, -39, -51, -31, -39, -17, 6, -25, -24, -16, 30, 8, -11, -23, -37, -18, -45, -30, -17, 38, 9, -12, 0, -30, -10, 30, 28, 9, 27, 31, -13, 0, -10, -8, -18, -38, 25, 36, -1, 17, 22, 48, -7, 28, 37, 20, 6, -22, -22, 4, -21, -30, -12, -25, 17, 8, -36, -14, -20, -33, 11, 26, -21, -56, -2, 39, -19, -4, 33, 47, -5, -27, 14, -8, 2, 22, -6, 18, 13, -8, -8, 43, -19, 14, -5, 23, -18, 0, 1, 6, -46, 4, 9, 19, -20, -10, 23, -6, 18, -20, 29, -43, 46, 0, 33, -25, 27, 24, -16, -4, 5, 40, -44, -27, -25, -56, -27, -35, -29, -38, 0, 21, 27, 18, 10, 29, 16, 0, -21, -5, -2, 33, 12, -30, -26, 24, -8, -4, -9, 34, -7, -10, 18, 40, -5, 37, -41, -11, 1, -15, -14, -19, -14, -41, 34, -2, 17, -44, 20, -31, 25, -10, -3, 22, 33, 0, 14, -17, 16, 25, -12, -9, -29, 4, 39, 17, -32, 17, 39, 29, -31, -10, 10, 41, -1, -38, -33, 38, -33, 17, -16, -23, -24, -23, 5, 20, -34, -24, 25, -28, 27, 20, 10, 10, -6, -37, -12, -27, -40, -40, 29, -1, 32, 21, -15, 17, 7, -13, 50, 10, -16, 10, -3, -16, -16, 43, -21, 37, 33, -14, -4, -36, -38, -10, -9, 6, -18, 6, 9, 9, -8, -25, -7, 33, -13, -3, -48, -18, 9, 47, -48, 5, 6, 18, 19, -20, 28, 46, -27, 10, 22, -8, -27, -8, -35, -2, -13, -8, 1, -6, -17, 12, 3, 14, 37, 4, 4, 22, 24, 3, -9, 25, 34, -24, -17, -14, 36, 25, 1, 25, -39, -3, 23, -18, 17, -31, 6, 43, -41, -50, -8, 6, -22, -25, -6, 3, 2, -19, -14, 21, 0, -11, -26, 47, 28, 7, -23, 40, 35, 29, -45, 6, 30, -34, 14, -32, -10, -28, -58, -13, -46, 2, -19, 9, -4, 3, 15, 44, -3, 22, 12, -9, -24, 9, -15, 24, 5, 11, -29, 35, 4, -18, 18, 22, 6, -61, 0, -31, -25, 38, -33, -16, 24, 42, -2, -6, 19, 16, -6, -14, 10, 46, -10, -43, 26, -13, 16, -4, -12, -13, -12, 5, -5, -30, 9, -29, 18, -15, -17, 19, 11, 26, -7, 4, 5, 7, 14, 47, 17, -8, -45, -11, -24, -37, -25, 6, -29, -4, 39, -28, 5, 10, 29, 34, 34, 8, -19, -14, 35, 14, 0, -40, 9, 24, -15, 6, 38, 16, 10, -21, -34, -2, -30, 32, 17, 6, -41, 31, -31, 1, -36, 10, -16, 6, 20, -13, -24, -20, -23, 45, -1, -19, 25, -3, 32, 6, 40, 51, 17, -9, -26, 11, 12, 27, 26, -16, -47, -7, -12, 0, 14, -15, 1, -31, -34, 11, 38, -15, -5, -2, 3, -45, 5, 5, 27, -35, -11, -1, 15, -30, 14, 23, -25, -40, -25, 19, -1, -19, 1, 17, 29, 10, 43, 22, 8, 1, 16, 19, 1, 26, -1, -45, 5, -26, -8, 42, -47, 27, -3, -24, -12, 30, -14, -27, 0, 35, -33, 23, -4, 47, -2, -13, -1, 31, 35, -24, 15, -47, -29, 28, 30, -11, 10, -2, 19, 35, -25, -6, 34, 0, -27, -2, -28, 12, 26, -9, -13, 34, 24, 20, 28, -46, 37, 44, 10, -21, -10, 10, -16, 31, -26, 36, 21, -19, 28, 14, 5, -16, -4, -15, 28, -13, -14, -7, 30, 25, -24, 9, 14, 22, 44, -16, -1, 20, -37, 17, -24, 23, -14, -22, -36, 22, 14, 11, -39, 24, 6, 6, -9, 34, 6, 10, 8, 15, 38, 5, 13, 23, 37, 18, 35, -30, 29, 12, -8, -22, -24, 25, 31, 30, 1, 11, -8, 48, 19, -20, -19, -10, -31, 44, -25, 47, -41, 10, 31, 28, 14, -14, 20, 32, -23, 5, 12, -19, 30, 9, 27, 15, -19, 19, -41, -15, 10, 19, -28, -14, -19, 15, -1, 35, -11, 31, -10, -39, 5, -7, -27, -40, 0, -18, -12, 5, -2, -5, 14, -16, 36, -35, 10, 41, -36, -37, 14, 44, -22, 5, -5, 7, 42, 36, -20, -3, -5, -23, 14, 21, -12, 16, 27, 22, -2, 24, -38, 28, 0, -40, -40, 14, 12, 3, 47, -26, 12, -31, -26, -23, -3, 10, 4, 45, 20, 23, -1, -34, 12, -15, -10, -31, -25, -18, -8, 26, -48, -5, -7, -5, 3, 8, -22, -21, 34, 22, -7, -32, 3, -6, 51, -52, 24, -6, -24, 27, -28, -15, -2, 31, 28, -1, -26, 1, 24, 32, 24, -33, -24, -10, 39, -43, 27, -14, -9, -10, -26, -33, 5, -21, 14, -40, 3, 8, -33, -14, -4, -13, -8, -24, -23, 0, 4, 5, -3, 51, -3, 24, 26, 0, 53, 2, 15, 16, 17, -11, -36, -38, 49, -32, 24, 23, -40, 4, -27, 42, 12, -41, 37, -15, 29, 12, 19, 46, -40, -18, 11, 16, 49, 1, -2, 4, -40, -31, 20, 4, -19, -2, -27, 20, 8, -6, 29, 50, -33, 6, -1, -47, -20, 11, -14, -29, -33, -7, -38, 40, 2, 2, 24, -26, 32, 26, -23, -38, -2, -18, 37, 14, -2, -3, -19, -29, -23, -1, -28, -11, -6, 13, 8, -19, 9, 9, 4, 30, -9, 31, 20, 24, 0, 21, -4, 12, -12, 26, 26, 7, 27, -22, -21, 24, -19, -4, 34, 9, -23, -12, 38, 23, 16, 14, -18, 33, 8, -3, -44, 34, -36, 42, 18, -19, 25, 34, -3, 31, 26, -27, 10, -6, -4, -24, 11, -12, -3, 10, -1, 24, 33, 0, 5, 23, -15, -24, -7, -1, 16}

#define TENSOR_DENSE_KERNEL_0_DEC_BITS {8}

#define TENSOR_DENSE_BIAS_0 {-26, -21, -85, -5, -99, 68}

#define TENSOR_DENSE_BIAS_0_DEC_BITS {11}

#define DENSE_BIAS_LSHIFT {0}

#define DENSE_OUTPUT_RSHIFT {7}


/* output q format for each layer */
#define INPUT_1_OUTPUT_DEC 4
#define INPUT_1_OUTPUT_OFFSET 0
#define CONV1D_OUTPUT_DEC 3
#define CONV1D_OUTPUT_OFFSET 0
#define LEAKY_RE_LU_OUTPUT_DEC 3
#define LEAKY_RE_LU_OUTPUT_OFFSET 0
#define CONV1D_1_OUTPUT_DEC 3
#define CONV1D_1_OUTPUT_OFFSET 0
#define LEAKY_RE_LU_1_OUTPUT_DEC 3
#define LEAKY_RE_LU_1_OUTPUT_OFFSET 0
#define FLATTEN_OUTPUT_DEC 3
#define FLATTEN_OUTPUT_OFFSET 0
#define DENSE_OUTPUT_DEC 4
#define DENSE_OUTPUT_OFFSET 0
#define DROPOUT_OUTPUT_DEC 4
#define DROPOUT_OUTPUT_OFFSET 0
#define SOFTMAX_OUTPUT_DEC 7
#define SOFTMAX_OUTPUT_OFFSET 0

/* bias shift and output shift for none-weighted layer */

/* tensors and configurations for each layer */
static int8_t nnom_input_data[900] = {0};

const nnom_shape_data_t tensor_input_1_dim[] = {150, 6};
const nnom_qformat_param_t tensor_input_1_dec[] = {4};
const nnom_qformat_param_t tensor_input_1_offset[] = {0};
const nnom_tensor_t tensor_input_1 = {
    .p_data = (void*)nnom_input_data,
    .dim = (nnom_shape_data_t*)tensor_input_1_dim,
    .q_dec = (nnom_qformat_param_t*)tensor_input_1_dec,
    .q_offset = (nnom_qformat_param_t*)tensor_input_1_offset,
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .num_dim = 2,
    .bitwidth = 8
};

const nnom_io_config_t input_1_config = {
    .super = {.name = "input_1"},
    .tensor = (nnom_tensor_t*)&tensor_input_1
};
const int8_t tensor_conv1d_kernel_0_data[] = TENSOR_CONV1D_KERNEL_0;

const nnom_shape_data_t tensor_conv1d_kernel_0_dim[] = {3, 6, 30};
const nnom_qformat_param_t tensor_conv1d_kernel_0_dec[] = TENSOR_CONV1D_KERNEL_0_DEC_BITS;
const nnom_qformat_param_t tensor_conv1d_kernel_0_offset[] = {0};
const nnom_tensor_t tensor_conv1d_kernel_0 = {
    .p_data = (void*)tensor_conv1d_kernel_0_data,
    .dim = (nnom_shape_data_t*)tensor_conv1d_kernel_0_dim,
    .q_dec = (nnom_qformat_param_t*)tensor_conv1d_kernel_0_dec,
    .q_offset = (nnom_qformat_param_t*)tensor_conv1d_kernel_0_offset,
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .num_dim = 3,
    .bitwidth = 8
};
const int8_t tensor_conv1d_bias_0_data[] = TENSOR_CONV1D_BIAS_0;

const nnom_shape_data_t tensor_conv1d_bias_0_dim[] = {30};
const nnom_qformat_param_t tensor_conv1d_bias_0_dec[] = TENSOR_CONV1D_BIAS_0_DEC_BITS;
const nnom_qformat_param_t tensor_conv1d_bias_0_offset[] = {0};
const nnom_tensor_t tensor_conv1d_bias_0 = {
    .p_data = (void*)tensor_conv1d_bias_0_data,
    .dim = (nnom_shape_data_t*)tensor_conv1d_bias_0_dim,
    .q_dec = (nnom_qformat_param_t*)tensor_conv1d_bias_0_dec,
    .q_offset = (nnom_qformat_param_t*)tensor_conv1d_bias_0_offset,
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .num_dim = 1,
    .bitwidth = 8
};

const nnom_qformat_param_t conv1d_output_shift[] = CONV1D_OUTPUT_RSHIFT;
const nnom_qformat_param_t conv1d_bias_shift[] = CONV1D_BIAS_LSHIFT;
const nnom_conv2d_config_t conv1d_config = {
    .super = {.name = "conv1d"},
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .weight = (nnom_tensor_t*)&tensor_conv1d_kernel_0,
    .bias = (nnom_tensor_t*)&tensor_conv1d_bias_0,
    .output_shift = (nnom_qformat_param_t *)&conv1d_output_shift, 
    .bias_shift = (nnom_qformat_param_t *)&conv1d_bias_shift, 
    .filter_size = 30,
    .kernel_size = {3},
    .stride_size = {3},
    .padding_size = {0, 0},
    .dilation_size = {1},
    .padding_type = PADDING_SAME
};
const int8_t tensor_conv1d_1_kernel_0_data[] = TENSOR_CONV1D_1_KERNEL_0;

const nnom_shape_data_t tensor_conv1d_1_kernel_0_dim[] = {3, 30, 15};
const nnom_qformat_param_t tensor_conv1d_1_kernel_0_dec[] = TENSOR_CONV1D_1_KERNEL_0_DEC_BITS;
const nnom_qformat_param_t tensor_conv1d_1_kernel_0_offset[] = {0};
const nnom_tensor_t tensor_conv1d_1_kernel_0 = {
    .p_data = (void*)tensor_conv1d_1_kernel_0_data,
    .dim = (nnom_shape_data_t*)tensor_conv1d_1_kernel_0_dim,
    .q_dec = (nnom_qformat_param_t*)tensor_conv1d_1_kernel_0_dec,
    .q_offset = (nnom_qformat_param_t*)tensor_conv1d_1_kernel_0_offset,
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .num_dim = 3,
    .bitwidth = 8
};
const int8_t tensor_conv1d_1_bias_0_data[] = TENSOR_CONV1D_1_BIAS_0;

const nnom_shape_data_t tensor_conv1d_1_bias_0_dim[] = {15};
const nnom_qformat_param_t tensor_conv1d_1_bias_0_dec[] = TENSOR_CONV1D_1_BIAS_0_DEC_BITS;
const nnom_qformat_param_t tensor_conv1d_1_bias_0_offset[] = {0};
const nnom_tensor_t tensor_conv1d_1_bias_0 = {
    .p_data = (void*)tensor_conv1d_1_bias_0_data,
    .dim = (nnom_shape_data_t*)tensor_conv1d_1_bias_0_dim,
    .q_dec = (nnom_qformat_param_t*)tensor_conv1d_1_bias_0_dec,
    .q_offset = (nnom_qformat_param_t*)tensor_conv1d_1_bias_0_offset,
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .num_dim = 1,
    .bitwidth = 8
};

const nnom_qformat_param_t conv1d_1_output_shift[] = CONV1D_1_OUTPUT_RSHIFT;
const nnom_qformat_param_t conv1d_1_bias_shift[] = CONV1D_1_BIAS_LSHIFT;
const nnom_conv2d_config_t conv1d_1_config = {
    .super = {.name = "conv1d_1"},
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .weight = (nnom_tensor_t*)&tensor_conv1d_1_kernel_0,
    .bias = (nnom_tensor_t*)&tensor_conv1d_1_bias_0,
    .output_shift = (nnom_qformat_param_t *)&conv1d_1_output_shift, 
    .bias_shift = (nnom_qformat_param_t *)&conv1d_1_bias_shift, 
    .filter_size = 15,
    .kernel_size = {3},
    .stride_size = {3},
    .padding_size = {0, 0},
    .dilation_size = {1},
    .padding_type = PADDING_SAME
};

const nnom_flatten_config_t flatten_config = {
    .super = {.name = "flatten"}
};
const int8_t tensor_dense_kernel_0_data[] = TENSOR_DENSE_KERNEL_0;

const nnom_shape_data_t tensor_dense_kernel_0_dim[] = {255, 6};
const nnom_qformat_param_t tensor_dense_kernel_0_dec[] = TENSOR_DENSE_KERNEL_0_DEC_BITS;
const nnom_qformat_param_t tensor_dense_kernel_0_offset[] = {0};
const nnom_tensor_t tensor_dense_kernel_0 = {
    .p_data = (void*)tensor_dense_kernel_0_data,
    .dim = (nnom_shape_data_t*)tensor_dense_kernel_0_dim,
    .q_dec = (nnom_qformat_param_t*)tensor_dense_kernel_0_dec,
    .q_offset = (nnom_qformat_param_t*)tensor_dense_kernel_0_offset,
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .num_dim = 2,
    .bitwidth = 8
};
const int8_t tensor_dense_bias_0_data[] = TENSOR_DENSE_BIAS_0;

const nnom_shape_data_t tensor_dense_bias_0_dim[] = {6};
const nnom_qformat_param_t tensor_dense_bias_0_dec[] = TENSOR_DENSE_BIAS_0_DEC_BITS;
const nnom_qformat_param_t tensor_dense_bias_0_offset[] = {0};
const nnom_tensor_t tensor_dense_bias_0 = {
    .p_data = (void*)tensor_dense_bias_0_data,
    .dim = (nnom_shape_data_t*)tensor_dense_bias_0_dim,
    .q_dec = (nnom_qformat_param_t*)tensor_dense_bias_0_dec,
    .q_offset = (nnom_qformat_param_t*)tensor_dense_bias_0_offset,
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .num_dim = 1,
    .bitwidth = 8
};

const nnom_qformat_param_t dense_output_shift[] = DENSE_OUTPUT_RSHIFT;
const nnom_qformat_param_t dense_bias_shift[] = DENSE_BIAS_LSHIFT;
const nnom_dense_config_t dense_config = {
    .super = {.name = "dense"},
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .weight = (nnom_tensor_t*)&tensor_dense_kernel_0,
    .bias = (nnom_tensor_t*)&tensor_dense_bias_0,
    .output_shift = (nnom_qformat_param_t *)&dense_output_shift,
    .bias_shift = (nnom_qformat_param_t *)&dense_bias_shift
};

const nnom_softmax_config_t softmax_config = {
    .super = {.name = "softmax"}
};
static int8_t nnom_output_data[6] = {0};

const nnom_shape_data_t tensor_output0_dim[] = {6};
const nnom_qformat_param_t tensor_output0_dec[] = {SOFTMAX_OUTPUT_DEC};
const nnom_qformat_param_t tensor_output0_offset[] = {0};
const nnom_tensor_t tensor_output0 = {
    .p_data = (void*)nnom_output_data,
    .dim = (nnom_shape_data_t*)tensor_output0_dim,
    .q_dec = (nnom_qformat_param_t*)tensor_output0_dec,
    .q_offset = (nnom_qformat_param_t*)tensor_output0_offset,
    .qtype = NNOM_QTYPE_PER_TENSOR,
    .num_dim = 1,
    .bitwidth = 8
};

const nnom_io_config_t output0_config = {
    .super = {.name = "output0"},
    .tensor = (nnom_tensor_t*)&tensor_output0
};
/* model version */
#define NNOM_MODEL_VERSION (10000*0 + 100*4 + 3)

/* nnom model */
static nnom_model_t* nnom_model_create(void)
{
	static nnom_model_t model;
	nnom_layer_t* layer[9];

	check_model_version(NNOM_MODEL_VERSION);
	new_model(&model);

	layer[0] = input_s(&input_1_config);
	layer[1] = model.hook(conv2d_s(&conv1d_config), layer[0]);
	layer[2] = model.active(act_leaky_relu(0.300000f), layer[1]);
	layer[3] = model.hook(conv2d_s(&conv1d_1_config), layer[2]);
	layer[4] = model.active(act_leaky_relu(0.300000f), layer[3]);
	layer[5] = model.hook(flatten_s(&flatten_config), layer[4]);
	layer[6] = model.hook(dense_s(&dense_config), layer[5]);
	layer[7] = model.hook(softmax_s(&softmax_config), layer[6]);
	layer[8] = model.hook(output_s(&output0_config), layer[7]);
	model_compile(&model, layer[0], layer[8]);
	return &model;
}
