#include "nnom.h"

/* Weights, bias and Q format */
#define TENSOR_CONV1D_KERNEL_0 {34, 32, -20, 4, -23, 1, -52, -39, -35, -47, 5, -49, -6, -57, 20, -48, 7, -39, 22, 7, 60, -52, 13, 0, 17, 25, 29, 1, -20, -45, 39, 18, 53, 21, -31, 6, -13, -23, 52, 24, 8, -16, -9, 49, -11, -32, 17, 47, -54, -4, 52, 31, 31, -44, 16, 69, 36, -11, 31, 45, 4, 18, 18, 48, -47, -38, -35, 58, 50, -49, 25, 10, 64, 37, 2, -8, -26, -3, 14, 48, -44, -40, -5, 14, 41, 26, 4, 35, 37, 23, -13, 59, -51, 12, 14, 62, -44, 30, -25, -17, 47, 49, 61, 2, -42, -17, -22, 51, 32, 44, -4, 40, -10, -53, -40, -22, -44, -15, -32, -59, -55, 58, 38, 50, -6, -19, 28, 0, -39, -42, -13, -17, -6, -2, -7, 8, 42, 45, -52, -5, -38, 29, -1, 16, -29, -47, 7, -55, -18, 50, -65, -50, -13, -5, -22, 5, 1, 42, -12, -22, 1, 25, -5, -39, -17, 15, -58, -23, 68, 32, 56, -12, -8, 56, 43, -30, -45, -35, 61, -11, 34, -18, 44, 68, 20, 41, 31, -55, 4, 59, -43, -44, -21, -16, 29, 42, 51, -19, 10, -60, 4, 44, -53, -55, 2, 18, 6, 22, 56, 40, -43, -15, 57, -33, -9, 40, 42, -73, -25, -27, -25, 35, -52, -61, 50, -37, -47, 40, 8, -17, 57, -11, 61, 29, 16, 65, 14, -4, -39, 32, 47, -43, 54, 15, 48, 13, -38, -44, 27, 34, -54, 49, 1, 24, 57, -15, 67, 18, -39, -67, -11, -9, 64, -31, 12, -18, 52, -21, 3, 2, 3, -2, 1, -13, -53, -2, -35, 22, 23, -49, 46, 47, 51, -34, -53, -45, 22, 15, -31, -57, -24, 15, -34, -12, -19, 37, 16, 12, -51, 35, -26, -50, 52, -28, -13, 47, 16, 39, -19, 16, 8, -49, -8, -29, -2, 30, -63, 40, -27, -38, -56, 46, -31, 26, 27, -33, 53, -62, -17, 14, -47, -35, -25, -51, 25, -16, -25, -44, -8, -37, -60, 15, 40, 22, 48, 41, -55, 32, -53, -22, 1, -29, -70, 17, -30, -5, -56, -2, 0, 16, -67, -12, 37, 39, -10, 48, 8, -56, -49, -44, -39, -4, 4, -40, -22, 17, -66, -24, -24, 58, -4, 5, -8, -16, 30, 39, -17, 21, -57, -3, 50, 31, -23, 57, 8, 24, -41, 53, -34, 17, 4, 8, -39, 44, -13, 35, 40, 1, 32, 5, -21, -35, -28, -13, -51, -57, -21, 61, -22, 9, -37, 24, 52, 44, -41, 11, 18, -43, 64, -14, -57, 62, -21, 59, 10, -21, -20, 38, -35, 46, -33, -43, 15, 8, -45, 22, 43, 7, -18, -16, 48, 59, -7, -54, -57, -51, 41, 54, -39, 24, -58, 38, -13, -7, -37, -17, -44, -2, 29, -57, 46, -57, -51, -45, 51, 6, -43, 52, -13, -22, -18, -35, -8, 35, -9, -17, 35, -11, -42, -43, -32, 40, 5, -49, -40, 5, 1, 22, 57, 58, -11, 23, -27, -43, -57, -12, -29, -41, -20, 9, 5, -48, -40, 2, 21, 58, -55, -6, 17, -36, -19, 60, 53, -45, 60, 8, -35, -33, 24, -41, 44, -40, 12, 33, 15, 65, 10, -19, 28, -15}

#define TENSOR_CONV1D_KERNEL_0_DEC_BITS {8}

#define TENSOR_CONV1D_BIAS_0 {19, 31, 27, -22, 35, -8, 42, -80, -50, -8, 33, 40, -5, -3, 92, -2, -50, 38, 60, 0, 37, 17, -19, 43, 35, 76, 47, 23, 28, 31}

#define TENSOR_CONV1D_BIAS_0_DEC_BITS {11}

#define CONV1D_BIAS_LSHIFT {1}

#define CONV1D_OUTPUT_RSHIFT {9}

#define TENSOR_CONV1D_1_KERNEL_0 {45, 23, 35, 50, -5, 37, -18, -26, -18, -54, -21, -20, 0, 21, 41, -14, -9, 35, 62, -39, 19, -35, 20, -38, 2, -31, -31, -34, 21, -23, 19, 48, -37, -16, 13, 12, -37, -2, 9, -43, -50, -52, 44, -15, 38, 27, -34, -54, -14, 27, -42, -14, 20, 4, 45, -7, 12, -30, 46, -23, -14, -38, 48, 14, 5, 19, -35, -41, -12, -61, 39, 7, -37, -9, 51, -7, -39, -4, 5, -33, 26, -6, 41, -23, 42, -1, 9, 30, 36, -14, -37, 47, -16, -36, -11, 37, -16, -29, -39, 18, -27, 45, -35, 35, 47, 64, -19, -28, 32, -26, 63, -59, 24, 54, -22, 36, -2, 38, 36, -4, 20, -15, -43, -52, 44, 29, -23, -24, 55, 11, 43, 47, 35, -7, 36, -6, 20, 56, 68, 42, 15, 11, 23, 33, -5, 16, -46, 50, 2, -21, 1, -20, -37, -23, -1, -7, 6, -8, -23, 24, -11, 9, 54, 2, 6, -35, 14, -3, -8, -41, -16, 47, -12, 52, -1, -38, 44, 15, -5, -29, 51, 4, -30, 4, 39, -29, 60, 43, 50, 35, -13, 30, 40, 15, 30, 27, 32, 57, 55, 27, -39, 29, -46, -59, -42, 30, -32, -41, 32, -32, 25, 4, 49, 26, -21, -51, 16, 17, 1, -7, 20, -44, -16, -44, 34, 47, -35, 11, -49, 46, -63, 8, -35, -47, 51, 15, 51, -37, 50, -28, 40, 12, -21, -54, 33, -46, 56, -42, 33, -5, 41, -18, -54, 10, 12, -21, -36, 36, 41, -56, -56, -20, -24, 1, -1, -39, 11, -6, 5, 5, -32, 21, 19, -27, -26, 22, 25, 0, 33, -13, 2, 35, 26, 52, 47, -11, -22, -41, -42, 49, 5, 18, 10, 53, 7, 2, 47, 11, 19, 43, -52, 22, 39, -13, -40, 2, -2, -7, -54, -47, -2, 36, -44, 47, -17, -4, 20, -5, 21, 7, 33, -34, 53, 11, 55, 7, -40, -10, -37, 19, -9, 44, -42, 37, 30, 13, 23, -26, -22, -6, -29, 5, 11, -54, 30, -27, -30, 30, -27, -25, -61, -6, -14, -26, 36, -43, 13, 35, -50, 46, 7, -11, -50, 10, -42, 1, 54, 10, 10, -48, -38, 57, 39, -2, -5, -37, 49, 15, -38, 40, -15, 15, -14, 4, -41, 3, -24, 19, 11, -47, 23, 45, -40, -35, -25, 42, 18, 40, -3, -5, 11, -1, -4, 31, -29, 55, 53, 36, -27, 33, -20, 12, -21, -18, 44, 32, -45, -58, 30, 13, -1, -20, -47, -46, 13, -14, -48, -19, 21, -10, 1, 11, 35, -34, 35, -29, -21, 54, -15, 50, -16, -32, -2, 12, -30, -20, -21, 15, 36, -48, 35, 33, 38, 58, 43, 43, -49, 41, 56, 10, -14, -3, 52, 5, -9, 13, -7, -36, -32, -18, 8, 12, -25, 37, 41, 51, -21, 45, 38, 2, -50, -44, 9, -28, 44, 50, -10, -27, -42, 13, -24, 12, 0, 29, 17, 66, -35, -25, -34, 5, 34, 27, -19, 45, -20, -34, 31, -3, -10, 50, -41, 0, -47, -11, 77, 54, 35, -41, -37, 21, -57, -3, -6, 9, -48, 41, -10, -29, -49, -7, -41, 63, 3, 10, 10, 19, -58, 39, -4, 5, -20, -12, 37, 15, 52, 29, 8, 40, -31, -50, -41, 53, -31, 8, -20, 55, 56, -37, -50, 3, 8, -59, 34, -20, -32, -15, -41, -24, -6, -5, -22, 14, -47, -23, -3, 50, -31, 10, 44, 17, 20, 17, -14, 36, 0, 61, 8, -52, -25, -26, -4, 19, -23, -1, -11, -9, -26, -12, 46, -11, -13, 43, -41, -50, 5, 11, -46, -27, 52, -24, 16, -42, 43, 34, 29, 54, 40, -28, 37, -17, 35, 5, -3, -26, 18, -32, 13, 18, 20, -19, -12, 7, -43, -26, 58, -31, 36, 3, -21, 31, -9, 13, -53, -14, 33, 7, -4, 19, -44, -11, 55, -27, -42, -13, 15, 12, 3, 38, 9, 8, -8, 38, -41, 43, -22, 6, -21, -3, -26, 12, -49, 34, -53, -27, 25, -39, -28, -34, 45, 22, 56, -39, -39, 18, 55, 67, 6, 19, 28, -1, 5, -34, 9, 43, 21, -16, -25, -43, -28, 13, 25, 7, 24, 23, -41, 23, 35, 63, 54, 41, 50, 47, -51, -19, -18, 0, 34, 45, 29, 43, 49, -34, -22, -34, 0, 12, 19, 5, -25, -13, -27, -6, 31, 20, -38, 41, 0, 46, -27, 47, 52, -13, -17, -55, 6, -33, 43, -1, 47, 33, -35, 11, 20, 34, 23, -7, -19, 11, 14, 40, -18, -39, 40, 35, -44, 24, 11, 7, -47, 25, 28, 50, -5, 46, -42, 23, 4, 0, -16, 42, -22, -5, 10, -11, -8, 8, -1, -48, 45, 13, 23, 5, -40, -15, -44, -1, 24, -29, 27, 1, 9, 55, 1, 31, 14, -1, -30, 0, 53, -58, -17, -17, -27, -11, -8, 14, -47, -18, 11, 11, 8, -17, -9, -24, -31, -25, -43, 17, -43, 46, 38, 8, 39, -58, -27, -20, 48, -29, 40, 27, -43, 43, 39, -9, 8, -56, -23, 38, 36, 18, 7, 51, -55, 19, 51, 5, 42, -26, -46, 44, -51, 66, -53, 31, 5, -49, 62, -15, 44, -5, 56, -28, 35, 14, -8, -18, -9, -23, -31, -55, 37, 32, 43, 11, -3, 58, 10, 19, 9, 7, -31, -24, -41, 37, 15, 14, -42, -47, 5, 9, -48, -37, 9, 12, 64, -35, 15, 25, -37, -7, 16, -50, -10, -31, -53, 24, -12, -22, -33, 0, -48, 55, -20, -41, 35, 4, -49, -40, -23, -41, -53, 25, -4, -36, 23, -19, -6, 7, -39, -32, 11, -23, -37, 9, -20, 26, -37, 17, -50, -26, -22, 6, 29, 31, -42, -11, -6, 20, -24, -16, 14, 36, -42, 29, 57, -12, 13, 0, 46, -14, 44, -18, 39, -11, 10, 33, 22, 38, 49, -18, -30, -30, 25, 43, -48, 54, 33, 36, 33, -21, 31, -39, 31, 36, -34, 8, 62, -48, 38, 25, -48, -44, 37, -61, -22, -14, -6, -43, -38, 36, 2, 12, 58, -55, -18, 41, 30, -32, 11, -52, 59, 27, -17, -26, -49, 3, 44, 30, -43, -7, -38, -54, -38, -37, 18, -43, -29, -53, 31, -7, 40, -13, 27, -56, -38, -10, -22, -53, -32, 44, -6, -46, -38, -49, -38, 45, -27, -27, 44, -1, -19, -56, 51, 40, 27, 35, -32, -43, 12, 1, -42, 3, 46, -13, -27, 32, 51, 25, -9, -16, -38, -20, 36, -17, -47, -54, 9, 38, -7, -10, -41, -29, -25, -32, -12, -43, -46, 59, 39, 57, 20, 55, 42, 49, -16, 38, 27, 17, 3, 10, 48, 52, 45, 14, -36, -43, 36, -22, -15, -35, 36, 7, -39, 49, -20, -37, 23, -17, -40, 2, -23, 40, 49, -36, 59, 12, 49, -41, -7, -44, 17, 7, 40, 22, -17, -25, 16, -43, -7, -15, 41, 21, -37, 25, -42, 35, 34, 20, 36, -1, -22, -34, 14, 15, 7, -4, 48, 0, 9, -5, -9, -6, 43, -5, -49, -18, -49, 39, -9, 11, 27, 30, 30, 35, -2, -38, 38, -64, -3, 30, -10, -42, -32, -43, 5, -42, -55, 50, 14, 24, -34, -45, -7, 35, 4, -1, -3, 16, 34, 53, 36, -30, -5, 4, -38, 18, -3, -35, -37, -6, 27, 45, -26, 27, -5, 5, 42, -34, 34, 27, 46, -38, -45, -18, -15, 35, 40, -20, -9, 55, -4, -27, 46, 45, 23, -12, 2, -19, 18, -11, -40, 21, 7, 5, 37, 35, 11, -37, 40, -35, -17, -35, 14, 4, 40, -19, 21, -17, -27, -20, 50, -9, -34, 9, -40, -43, 26, -44, -26, -27, -15, 49, -18, -44, -43, 44, 58, 10, 26, 56, 64, 60, 25, -21, 19, -44, 45, 11, 15, -27, 41, -41, -9, 4, -34, 28, -5, -10, 44, 12, 50, -49, 3, -42, 30, -39, -14, 12, 3, -2, 6, 49, -43, 57, -17, 55, -48, 29, -45, -7, -48, -59, 12, -27, 20, -15, -10, -16, 4, -14, -7, 27, 30, 12, -36, -13, -34, 17, -56, 2}

#define TENSOR_CONV1D_1_KERNEL_0_DEC_BITS {8}

#define TENSOR_CONV1D_1_BIAS_0 {6, 4, 3, 8, 0, 0, -5, 4, -6, 1, -4, 0, 4, -1, 4}

#define TENSOR_CONV1D_1_BIAS_0_DEC_BITS {8}

#define CONV1D_1_BIAS_LSHIFT {0}

#define CONV1D_1_OUTPUT_RSHIFT {8}

#define TENSOR_DENSE_KERNEL_0 {13, -19, -47, -92, -36, -81, -5, -54, -42, -88, -6, 46, -41, 78, -41, -59, 54, -10, 46, -36, 94, 27, 67, -33, -20, 93, -29, -23, -7, -87, -29, -3, 11, 44, 26, -2, -47, 76, -29, -20, 10, 2, -50, -78, -40, 7, -13, -34, -39, 52, 6, 76, 64, -64, -60, 46, 36, -8, -77, -59, 19, -70, -76, -62, -21, 4, -48, 33, -17, 2, 66, -64, -22, 17, -87, -3, -20, 33, 19, -52, -56, -9, 22, -57, -53, -93, 80, -55, -32, -1, -17, -68, -7, 36, 40, 5, 19, -63, -33, -31, -52, -6, -62, 7, 30, 22, 43, -12, -10, -40, -24, -45, 25, 37, 58, 16, -4, -22, -3, -39, 0, -15, -59, -31, 52, 34, -16, -31, 87, 6, 40, -56, -69, 1, -27, 18, 49, 62, 5, 13, -65, -67, -9, -76, 41, 68, 39, -17, 44, -65, 30, -17, -19, 46, -11, -79, -34, 10, 4, 45, 78, -80, 70, -23, 14, 15, 64, 30, 81, -2, -75, 63, -69, 58, -15, -43, 41, 26, 27, 10, -47, 18, -98, -44, 37, 10, 81, 11, 8, -17, -4, 49, -35, -58, -41, 81, 25, -62, -54, 18, 9, 2, 43, -30, 33, -14, 41, -71, 22, -50, 32, -34, -25, 0, 47, 50, 26, -53, -3, -16, 66, 14, -12, 79, 67, 46, 27, 58, 67, -10, 28, 63, -29, -4, 42, 53, 39, 37, 40, 11, 72, -44, 48, 32, -94, -55, -63, -21, -60, 56, -52, -45, -87, -25, 75, 29, 16, 14, -33, -29, 51, -9, -59, -98, -2, 62, -63, 66, -50, 10, -19, 91, 52, 67, 33, -31, 28, 26, -51, 53, 29, -12, -38, -58, -30, -72, 14, 35, 57, 41, 6, -51, 13, 69, 40, 26, 51, 41, 52, 14, 59, 62, -26, 37, -74, -34, -61, -74, 19, -3, -71, -10, 72, -51, -25, 0, -9, -28, -32, 45, -32, -44, -61, 10, 48, -60, -19, 56, -66, 31, 41, 88, 50, -85, 4, -40, 24, -9, -29, 57, -67, 8, 76, 51, 10, -15, -54, -48, 21, -21, 23, 13, 65, -47, 12, -1, -66, -54, -26, -83, 14, -5, -68, 15, -2, 12, -67, 19, 22, -34, 76, 23, 4, 46, 46, -20, -33, -38, -17, -21, 27, 56, 65, 78, 30, -43, 6, 48, 47, 17, 46, -34, -63, 5, 9, -39, 44, 61, -47, -33, -30, 29, -15, 26, -23, 62, 30, 29, 25, 52, 47, 79, 12, 28, 61, 52, 66, 41, -20, 41, 45, -30, -78, 58, 11, -8, -14, -46, -59, -54, 23, 28, 1, -69, -47, -2, 50, -45, 21, -21, 74, 58, -36, -21, -65, -31, 19, 58, -77, 74, 77, -58, -47, 45, 3, 43, -50, 10, -60, -37, 6, 37, -18, -16, -37, -45, -13, 52, 92, -68, 42, 1, -20, -59, -65, -46, 50, -60, -32, 12, 27, 24, 95, -57, -81, -87, -63, 67, -48, -30, 7, 62, 22, -40, -43, 67, 8, -10, 14, 37, -61, -40, -71, -68, -41, -58, -46, -20, -70, 46, 18, -11, -40, 62, -54, -29, -59, 70, 72, -1, 40, 39, 48, -82, -53, -65, -7, -34, -89, 7, -60, -47, -26, 39, -26, 57, 55, 56, 67, -14, 28, -81, -22, -47, 13, -5, 2, 16, 23, 29, 69, -28, 0, -73, -58, 56, 9, -4, 25, 31, 15, -17, 26, 84, -90, 55, 72, 78, 81, 59, 3, 12, -40, 6, 26, 43, -49, -37, 68, 35, 28, 9, 88, 36, -21, -23, 2, 2, -63, 9, 9, -13, 73, -13, 65, 11, -79, -93, -76, -38, -87, 73, -35, 13, 81, 60, -34, -67, 57, -61, -69, -5, -18, -63, 23, 41, 50, -55, -52, -37, -60, -5, 9, 86, -6, 53, -53, 10, -52, 13, -23, 53, -35, -42, -71, 8, 65, 30, 44, 37, -32, -21, -27, 46, 19, -11, 4, 25, 88, -41, 24, -34, 44, -58, -75, -8, -41, 45, -48, 24, -57, 36, 84, 20, 54, -5, 10, 9, -9, 25, -82, 85, 31, -44, 59, -51, -17, -75, -112, 19, -55, 50, 54, 82, -58, -3, -38, 18, 51, -10, 2, -38, -38, -76, -12, -20, -5, -14, -99, 51, 15, 87, -24, 4, -54, 18, 62, 51, 66, -9, 67, -57, -21, 2, -36, 47, 3, 28, 20, 57, 77, 18, -32, -10, 28, 9, -34, -46, -16, 82, 11, 55, 30, -63, 14, -49, -20, -20, -16, 29, 6, 24, -50, -73, -42, 21, -86, 61, -58, 78, -87, 3, -18, 40, -61, -4, -1, 74, -42, -60, -7, 0, -4, 1, -48, 23, -49, 51, -41, -66, 7, 4, -4, -38, -28, -63, -45, 59, 11, -92, -37, -13, -19, -18, -61, 99, -19, -32, 72, -47, -8, -35, 77, -37, -29, -27, -12, 23, 13, 17, 4, 103, -31, 22, 0, 20, 23, 75, 99, -31, -72, 68, 26, 8, -93, -22, 12, -52, -10, 20, 29, -85, 46, 54, 35, -50, 21, 65, -53, 22, -26, -98, -41, -49, 65, -98, 75, 69, 15, 34, -51, -39, 26, -53, -32, -12, -18, -64, 15, -60, 34, -39, 7, -78, 57, 77, 0, -59, -53, -7, 11, -97, -12, 79, 34, 44, -73, -54, -6, 49, -63, 62, -29, 12, -20, -68, 52, 59, 26, 11, -26, -13, -104, -42, -9, -60, 0, -9, 12, -40, 13, 67, 24, 70, 42, 57, 13, -32, 36, -47, -61, 56, 95, 36, 33, -45, -25, 8, -74, 103, 38, -3, 62, 57, -64, -37, -9, 21, -61, 97, 21, 38, 35, -24, -67, 4, 23, 57, -23, -83, -41, -66, 69, 67, 70, -59, 20, 75, 3, -37, 52, 24, 26, -19, 63, -60, -4, 48, -33, -55, -64, 41, -66, 77, -9, 1, -18, 23, 20, 42, 69, 13, -29, -1, -89, 48, -94, -57, 62, -15, -64, -17, 41, 74, -46, -63, 13, 4, -92, 46, -56, 89, -59, 61, 33, -19, -68, 36, 60, 47, -16, 12, -43, -41, 44, 1, 39, 38, 49, 42, -14, -78, 1, -12, 6, -35, -53, 22, -102, 73, -87, 33, -45, -24, -21, 68, 63, 9, -18, -5, -16, 22, -43, -66, 22, 45, 22, 12, -51, -35, -30, 3, -103, 9, -28, 44, -48, -57, -1, 29, 71, 60, -79, -28, -18, -36, -68, -25, -10, -90, 18, 40, 25, -76, -21, -30, 40, -15, 93, -53, -33, -37, -79, -7, 49, -54, -34, -41, -69, -14, 79, 76, 25, 88, -69, 10, -1, -70, 4, -11, -7, -44, -61, -55, 92, 22, 56, 31, 13, -55, 59, -42, 13, 41, -63, -7, -21, 84, 56, -92, 1, 87, -70, 69, -20, 5, 67, -46, -64, 10, -47, -11, -12, -82, -46, 53, 4, 64, 35, -40, 26, 21, -24, -6, -63, 69, -23, 11, -22, -61, -8, 38, -54, 20, 35, 12, -27, -11, 10, 8, 71, -17, 83, -57, 2, 42, -56, -46, -29, 18, -72, 97, -42, 24, -72, -38, -2, -11, -56, 17, 31, 55, -79, 55, -61, 29, 27, 0, 20, 47, -78, 14, 70, 34, 66, -68, -70, -17, -3, -1, -27, 21, -5, -76, -34, -1, 27, 62, 48, 32, -13, -21, 47, -27, 8, 29, 75, -56, 46, 9, -77, -32, 89, 35, -41, 8, 30, -8, -58, -63, -29, -61, 4, 2, -50, 0, -4, 15, 66, -48, 42, -110, -13, 42, 34, -7, -50, -49, 19, 91, 26, -89, 82, -25, 56, 47, -47, -20, 3, 5, 107, 62, -48, -25, 52, 36, -70, -75, 46, 0, -62, -20, 83, -27, -35, 85, -55, -16, -9, -32, 25, -53, 106, 11, 37, -11, 15, 10, -48, -25, 53, 58, 89, 0, -25, -14, -68, -16, -43, -7, -33, -45, -38, -22, 29, 72, 30, -26, -29, 20, 46, -52, -39, -13, 28, -81, -13, 65, 31, 60, -54, -44, -63, 59, -22, 36, -71, 0, 32, -19, 20, 52, -69, -86, -14, 49, -39, 46, 44, 65, 64, 23, -28, 49, -101, 2, -11, -11, -99, -55, -31, -91, -87, -35, 42, -8, -39, -56, 59, 18, -28, 7, 21, -106, -52, 1, -21, -6, -57, -59, -45, -22, -74, -6, 17, 25, -15, -48, 13, 30, 35, -18, 24, -45, -45, -55, -61, -26, 87, -51, -86, 28, 18, -36, -92, -105, -5, -67, 54, -70, 57, -33, -48, -18, -80, -29, -11, -61, 39, 0, -75, -19, 15, 7, -89, -62, -67, -106, 37, -58, -8, 49, 32, -33, 17, -6, -29, -82, -1, -10, 27, -56, -4, 27, -70, -97, -29, 3, -29, 35, 98, -78, 24, 22, -11, 71, 83, -29, 39, -10, 27, 4, 41, -33, 57, -26, -2, -53, 21, -40, -5, 42, -86, 73, -1, -21, -74, -13, -90, -27, 35, -76, 2, -56, 43, 50, 36, -87, 8, 23, -49, -33, 41, 41, 70, -33, 54, -56, 20, -93, -34, -45, 33, -23, 46, -20, -74, 29, -34, -71, -2, 27, -45, 59, 33, 41, 16, 21, 47, -45, -36, -33, 29, -45, 58, -67, -66, 3, 9, 65, 42, -5, -41, -14, -68, 83, -35, 12, 22, -1, 60, -75, 57, -60, -58, 65, -65, 38, -11, 46, 60, 13, 59, 45, 36, -48, 35, 19, -24, -74}

#define TENSOR_DENSE_KERNEL_0_DEC_BITS {9}

#define TENSOR_DENSE_BIAS_0 {-16, 20, -25, -74, -55, 83}

#define TENSOR_DENSE_BIAS_0_DEC_BITS {11}

#define DENSE_BIAS_LSHIFT {1}

#define DENSE_OUTPUT_RSHIFT {9}


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
#define DENSE_OUTPUT_DEC 3
#define DENSE_OUTPUT_OFFSET 0
#define DROPOUT_OUTPUT_DEC 3
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
