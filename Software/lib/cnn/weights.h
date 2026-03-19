#include "nnom.h"

/* Weights, bias and Q format */
#define TENSOR_CONV1D_KERNEL_0 {-53, -51, -44, -37, -35, -36, 41, -43, -42, 9, -36, 1, 17, 0, -19, -41, -6, -23, -58, 62, 1, -24, -53, -18, 26, 51, -34, -25, -16, -14, 59, 55, 51, 62, -58, 46, -54, -53, -51, 42, -44, -24, 58, -8, 28, 40, -50, -42, -47, 11, -14, 38, 17, -27, 7, -9, 36, -11, -31, 52, -39, -11, 5, -65, -18, 46, 17, 2, 56, -29, -36, 61, -23, -54, 58, -5, -4, 22, -16, 32, -58, -43, 38, -28, -3, -23, -27, 10, 2, -39, 44, 48, 60, 62, -17, -4, 20, -41, 39, -42, -32, 1, 56, -63, -59, 50, 37, -9, 59, -56, 0, 51, 59, -23, 56, 56, -4, -37, 10, -12, -26, 42, -1, -45, 19, -38, -18, 31, -20, 45, -2, 51, 37, 59, 66, -37, -5, -4, -30, 15, 66, -46, 56, 23, 20, -42, -24, -8, 32, 26, -32, -63, 57, 34, -52, -8, -1, -13, -59, 23, -33, -55, -19, 22, -37, -30, 4, -31, -43, -24, -51, 23, 49, 1, 10, 10, -48, -2, 7, 42, 4, -59, 16, 36, -4, -39, 6, -32, -17, -13, -43, 45, 52, 45, -43, 13, -54, 48, 59, -39, -17, -30, 28, 18, -43, 34, -61, -46, 45, -30, -38, 16, 49, -52, -65, 26, -33, -15, -44, 9, -9, 49, -37, -16, -18, 33, 55, 38, 49, -55, 9, -41, 38, -27, -32, 54, 58, 13, -17, -65, 64, -21, -27, 39, -42, -55, -65, -17, 25, -19, 41, 60, 29, -64, 11, 45, 5, 1, 42, -47, -23, -30, 65, -7, -22, 59, 5, -43, -60, 52}

#define TENSOR_CONV1D_KERNEL_0_DEC_BITS {8}

#define TENSOR_CONV1D_BIAS_0 {-53, 26, -58, 15, 24, 21, 49, 44, 59, -66, 66, -35, -25, -55, 54, -21, 62, 59, -12, -56, 61, -30, 53, -19, -38, -24, 70, -1, -69, 69}

#define TENSOR_CONV1D_BIAS_0_DEC_BITS {12}

#define CONV1D_BIAS_LSHIFT {0}

#define CONV1D_OUTPUT_RSHIFT {8}

#define TENSOR_CONV1D_1_KERNEL_0 {-41, 98, 19, -94, 60, -15, -79, 41, 72, -19, 15, 75, -39, 17, 19, 89, -32, -92, 84, 85, -112, -83, -74, -70, 38, 72, -28, -79, -24, -97, 29, 61, -46, -76, -47, -79, -70, 63, -13, 94, -72, -31, -79, 90, 26, 44, -70, -61, -65, -81, 27, -41, -98, -82, -72, -13, 12, -47, 42, 52, -1, 102, -19, 28, 0, -63, -41, -16, -37, 90, -4, -27, 50, 41, -38, 60, 3, -5, 35, 53, -32, 20, 12, 45, 42, 64, -11, 29, -34, 48, -108, 38, 14, 4, -27, 102, -86, -2, 90, -39, 10, 28, -77, 22, 63, 18, 67, 33, 98, 36, -11, -27, 26, -5, -24, -100, 58, -65, 31, -36, 5, -51, -34, 52, 48, 19, 9, -39, -95, 2, -25, -85, -41, 72, -54, -16, 90, -11, 73, 19, -26, -26, 25, 35, -5, -43, -32, 16, 47, -31, -11, -104, -55, 10, 106, 75, 84, -18, 70, -101, 55, 4, -31, 82, 69, -24, -22, -95, -53, -74, -53, 76, 86, -45, -22, 78, -60, -74, -44, 98, -28, -6, -54, 90, -17, -81, -86, -109, 93, -7, -43, -29, 26, -68, -38, 35, -60, 31, -7, -26, -57, -59, 31, 41, -19, -20, 112, -109, -36, 16, 19, -50, -71, 102, 76, -17, -46, -106, -100, 93, 109, 43, 20, -110, -38, -66, -44, 42, -29, -14, 71, 42, -21, 12, 1, 65, 97, -96, -19, -29, -112, 1, -25, -33, 26, -52, 20, 25, 80, -114, 97, -54, 55, -98, 34, 31, 21, -41, 14, -100, -96, -87, 23, -74, -89, 8, -6, 90, -48, 100, -89, -88, -23, -95, 102, 103, -56, 57, -54, -52, 25, -29, -4, -18, -25, -7, -111, 67, 0, 77, -30, -53, 106, -63, 97, 91, 5, -12, -69, 55, 67, 59, 87, -11, 60, 38, 95, 29, -3, -14, -70, -100, 3, 86, 97, 48, 41, -64, 105, -94, 50, 23, -80, 107, 49, 44, 14, 6, -92, -11, -88, -41, 59, 78, -72, 71, -79, -101, -40, 41, 62, -48, -19, -49, -93, 95, 104, 7, 79, 44, -67, 82, -83, 61, -49, -10, -76, -22, 93, -12, 44, -58, -30, 107, 84, -1, -94, -22, -96, 11, 46, -54, 1, -79, 36, -111, -18, -38, 70, 2, -66, -66, -110, 22, -23, 87, 31, 23, 34, -74, 1, -104, -80, 20, -89, -93, -45, -106, 48, -7, -95, -76, -41, 21, -18, 65, -44, 30, -53, -100, -34, 45, 83, -19, 98, -42, 109, -74, 68, -9, -66, -32, -32, 84, -99, 113, -73, 12, -10, 11, 12, -91, 46, 7, 22, -32, 44, -74, 18, -67, 61, -42, -23, 72, 50, 67, -8, 35, -61, 84, -15, -78, -56, -51, -5, -74, -90, -7, 94, 16, -58, 93, 27, 30, -81, -25, 109, 32, 74, 92, -93, -67, -92, -48, 82, -11, 71, 57, -65, 35, 72, -84, -87, -101, 47, 2, -47, -18, -38, 48, -21, -69, -33, -60, 67, -88, -49, 15, 109, 77, 12, -70, 9, 18, 43, 19, -30, -103, -98, 19, 33, 9, -88, 90, 61, -2, -104, -31, 76, 1, -17, -75, 18, -37, 30, 63, -14, -14, 34, -44, 39, 33, 87, 44, -39, -66, -38, -102, 75, -94, -72, -74, -108, -87, 6, -43, 96, 6, 103, 25, -102, 98, 95, 77, 69, 28, 0, 60, 22, -95, 62, 19, 92, -51, -45, 68, -19, 83, -63, -20, -5, -82, -65, -72, 44, -77, -100, 55, -80, 87, 82, 6, -72, 58, 36, -3, -22, -79, 40, 80, 35, 98, -60, 62, -41, -83, 99, -5, 19, 108, -58, 29, 66, 51, -76, 52, -57, 85, -58, -47, 110, 23, 32, 44, 46, 105, 75, -6, -38, 52, -24, -33, -58, -20, -68, -114, -93, 37, -24, 11, -90, -47, 49, -33, -94, 20, 5, -114, 5, 97, 47, 12, 80, 8, 11, -98, -110, 15, -88, 113, -16, 91, -43, -22, -15, 7, -79, -34, 8, -64, 24, 31, -10, 72, -19, 91, 7, -51, -113, -7, 110, 90, 0, -18, -23, -42, -38, -49, -93, 55, 103, 69, -16, 82, 73, 17, 77, -74, -90, 19, -100, -96, -55, -11, 72, 85, 2, -26, -49, -74, 20, -37, 72, -66, -7, 6, -77, -18, 46, 11, -19, -45, 10, 54, -85, 52, -21, -74, 55, 8, 84, 45, 97, 15, 7, 31, 35, -33, -94, 7, 73, 4, 2, 99, -9, 1, -32, 11, -92, 20, -44, -96, 81, 22, -37, 87, -45, 67, -20, 103, -87, -96, 2, 27, 109, 7, -94, -36, -48, 95, -53, -15, -85, -58, 83, 91, -90, 1, -14, -100, -104, -15, 59, 99, -41, 63, -98, 87, 45, -90, 84, -66, -90, -12, -55, -43, -87, 5, 39, 80, -48, -27, 72, -64, -98, -50, 24, -52, 99, 63, -96, -79, 81, 57, 22, 24, 33, 13, -10, -49, -75, 31, 50, 87, -35, -63, 79, 41, 43, -22, 16, -15, -37, 81, -75, -55, -14, 62, -76, 99, 71, -65, -72, -30, -76, 54, 8, 19, 34, -89, 56, 92, -14, 0, 89, 71, 16, -57, -63, -11, 88, 10, 96, -81, 14, 55, 79, 48, 73, -58, -97, 75, 26, -66, 4, -84, 27, 54, -8, 6, -70, 40, -47, -55, 68, 5, -103, -71, 30, -50, -39, 55, 86, 73, 76, -66, 27, -100, -75, 62, 36, 89, 61, -74, -65, 86, -37, -27, -35, -16, -109, 16, 40, 98, -51, -46, -106, -68, 34, -25, -15, 13, -29, -37, -74, -71, -101, -9, -10, -71, 49, 87, 56, -68, -65, 14, -93, -88, 15, 11, -91, -10, -2, 85, 70, -20, 68, -93, 55, 113, 57, 10, 97, 68, -40, 39, 27, -49, 97, -27, 6, -86, -57, 32, -88, 50, -32, 37, -99, 7, 37, -47, 0, 11, -14, 99, -71, -48, 21, -96, -91, -20, 77, 79, 18, 97, -88, 55, 27, 41, -13, -77, -97, 109, -4, 65, 82, 48, 35, 0, 23, 93, -7, -44, 38, 14, -32, 14, 24, -63, 10, 80, -106, 77, -10, 66, 84, 34, 57, -23, -55, -19, 26, 69, 91, -24, 34, 87, -98, 79, -96, 26, -40, -52, -27, 52, 99, 23, -6, -13, 75, -30, 55, -61, -16, 13, -59, 15, -46, -105, 47, -105, 88, 83, 5, 30, -93, 2, 13, -94, -105, 5, 57, -75, -50, 10, -15, -53, 37, 98, 92, -88, -63, -66, 100, 65, -19, 64, 93, 86, 60, -57, 98, -98, -18, -30, 41, 62, -84, 76, -74, -93, 46, -11, 88, 63, 98, -16, 27, 2, -59, -55, 14, -39, 46, -94, 52, -28, -22, -46, 96, 54, -4, -34, -69, 37, 40, 85, -36, 47, -39, 49, -112, 78, 92, 89, -39, 91, 18, 13, 81, -28, 49, 84, 18, -97, -44, 44, -41, -65, 39, 18, 53, 70, -92, -51, -100, -104, 29, -104, -103, 39, 33, -64, -16, -102, -21, 21, 29, -31, 20, -79, -76, 1, 77, -100, 98, -4, 76, -46, 46, -84, 66, 16, 62, -36, 5, -71, 80, -27, 76, -10, -55, 36, -97, -8, 27, 110, 11, -43, -43, -60, 86, -1, -32, -100, -106, -112, -82, -4, 88, 74, -4, 29, 98, -54, -96, 62, -19, -49, -99, 69, 9, -87, 92, 71, 95, -72, 51, 93, -57, 44, -77, 113, 34, 26, 62, 94, -10, 17, -39, -81, -83, -101, -48, 20, -29, -17, -49, 24, 22, 88, 8, -101, 71, -108, 47, 91, 22, -22, -78, 90, -13, 39, 92, -60, -15, -34, 41, 91, -88, 43, 64, 14, -18, -25, -62, -42, -1, 62, 38, -53, -55, -89, 54, 2, -50, -8, 67, -14, -21, -10, -34, 37, -66, -32, 59, 74, -35, 18, 111, 69, -35, 96, 43, 91, 76, -92, 33, 27, -72, -98, 22, -28, 29, 46, -111, 12, -8, 65, 99, -60, 28, 82, -49, -58, -64, 15, 84, 17, 77, 13, -4, -92, 54, -73, 80, 37, -92, -103, 18, -56, -105, 76, -6, 68, 89, 30, 32, 18, -17, 115, 27, 77, 110, -86, 5, 91, -100, 100, 13, -9, 61, 9, 63, -23, 22, -83, -35, 79}

#define TENSOR_CONV1D_1_KERNEL_0_DEC_BITS {9}

#define TENSOR_CONV1D_1_BIAS_0 {-52, 25, 43, -53, -41, 60, -1, 53, -68, 0, -52, 72, 54, -16, -33}

#define TENSOR_CONV1D_1_BIAS_0_DEC_BITS {12}

#define CONV1D_1_BIAS_LSHIFT {1}

#define CONV1D_1_OUTPUT_RSHIFT {9}

#define TENSOR_DENSE_KERNEL_0 {30, -8, -40, -42, -47, -10, 57, 53, -8, -73, 41, -25, 7, 73, -23, -4, 65, 18, 27, 55, -71, 23, -37, 42, 34, 75, 78, 15, 27, -77, 74, -18, 57, 41, -61, 2, 42, 60, -36, 26, 38, -30, -75, -28, -42, -26, -18, -80, -52, 40, -42, 59, -42, 25, -43, 48, -47, -43, -65, -24, -7, 34, 71, -17, 12, -24, -18, 37, 50, -13, -28, 67, -26, -54, 45, 20, -41, 29, -11, -49, 3, 3, -1, -7, 54, 70, -48, -77, -72, -16, 12, -17, -63, 66, 55, 27, -53, 18, 57, -36, -4, 57, -14, 39, 74, 68, -18, -64, 12, 51, -40, -31, 23, 37, -29, 41, 14, -42, -64, -1, 81, -46, 76, -47, 13, 51, 3, -16, 23, -2, 46, -41, 27, -4, 56, 38, 82, -19, 81, -17, -47, 75, -35, 4, -52, 49, -29, -28, 75, 24, 57, -31, -61, 49, 3, 10, 3, -71, -65, 5, -9, -11, 7, 45, 54, 14, -6, -68, 13, -28, 14, -60, 15, 7, -60, 66, -69, -29, -33, -56, 18, -12, -27, -58, 62, 69, -30, -70, -48, 16, -18, -37, -46, 67, 61, -67, 48, 29, -61, 34, -14, -28, 18, -5, -10, 10, -47, 61, 9, -13, 29, 48, -24, -68, 1, -1, 72, -24, -32, 21, -50, 50, 51, -24, 71, -7, 18, -41, -29, 69, -12, 16, 80, 2, 7, -37, -57, -57, 14, -44, -57, -10, 63, -77, -2, -24, 0, 40, -44, 14, 74, 66, -8, -47, 74, 53, 37, -28, -8, 28, 2, -28, -9, 47, -18, -44, 5, -70, 22, 41, -16, 40, -42, 53, 61, 54, -46, 82, -64, 9, 34, -70, 2, -66, 43, 40, 20, 13, 17, -27, -81, -32, 46, 20, -31, -45, 3, -50, -42, 22, -34, -28, -5, 16, 59, 3, 23, 70, -15, -22, 51, -61, -6, -66, -5, -29, -30, 29, 7, -47, 29, 5, 60, -67, -44, -28, 74, -66, -48, 2, -35, 19, -74, -15, -63, -79, 21, 58, 52, 30, -30, 13, -27, 81, -76, -57, -18, -85, -8, -77, 32, -43, -31, 16, -61, 72, 33, -30, -18, 5, 7, -27, -69, -83, -56, 15, -39, -76, 14, -38, -78, 31, -45, -28, 30, -67, -1, 0, 49, -2, 57, 47, -61, -22, -20, 16, 18, 12, -36, 44, 1, -6, -74, 45, 28, -3, -34, -30, 50, 27, 39, -67, 3, -61, -68, 3, -63, -71, -11, 54, -5, 30, 40, -49, -19, -66, 14, -45, 52, 63, 65, 23, 42, 67, -47, -57, -1, 4, -1, -60, 10, -65, 71, -33, 76, -71, 16, -47, -17, -14, 68, 64, 25, 64, -73, 49, 38, 20, 19, 32, 11, 71, -58, -2, 72, -9, -56, -40, 33, -17, 19, -43, -29, -46, 24, 55, 72, -81, -6, 73, -30, -7, -66, 51, 28, -25, 52, 6, 26, 2, 59, -71, -35, 82, -42, 28, -21, -8, -64, 16, 0, -68, -30, 61, 41, 82, -21, -9, 70, 28, 11, 59, -32, 26, -7, 58, 47, 30, -54, 40, -70, 37, 55, 2, -7, -66, -12, -84, -5, -24, -36, 1, -59, -66, 22, 50, 40, 53, -77, -13, -38, -36, -63, -58, 16, 14, 26, -39, -52, 7, -31, 21, 74, 42, 9, 47, 39, 54, 62, 3, -61, 69, -11, 33, 3, -54, 20, -24, -76, 48, 46, 60, -28, -27, 9, 76, -30, -38, -63, 43, -77, 43, 57, 67, 3, 53, 68, 15, 22, -20, -73, -40, -63, -79, 44, -50, -18, -6, -66, 40, 64, -19, 4, -69, -42, -9, 37, 47, 17, 48, -26, 3, -20, 4, -44, 21, 47, 48, 31, -71, 21, 7, 37, 82, -24, 16, 20, -2, -16, -32, -17, -63, -60, 81, -49, -52, 38, -28, 55, -70, -21, -32, -35, 34, 60, 55, -31, -64, -34, 50, -12, 57, -41, -46, -61, 48, 31, -53, 65, -49, 40, 49, 82, -52, 21, -2, 73, 25, -39, 49, -5, -57, -8, 20, 40, 79, -3, 45, -35, 60, 32, -57, -55, -76, 8, -40, -10, -35, -46, -69, -23, -26, 69, -78, -22, 77, 4, 18, 54, -14, -66, 11, -9, 69, 17, 3, -69, -11, -20, 5, 44, -9, 69, -9, -25, 11, -3, -70, 7, -43, 35, -83, 56, -45, -74, -68, -19, 20, -44, -37, -30, -36, -19, -57, 40, 69, 59, -78, -48, 46, 40, 13, 39, 74, 54, 46, 25, 53, -83, -11, -12, -33, 30, -57, 3, -71, -15, 65, -66, -1, -18, 52, 72, -8, -47, -69, 45, 47, 52, -54, -48, 22, 85, -29, 4}

#define TENSOR_DENSE_KERNEL_0_DEC_BITS {9}

#define TENSOR_DENSE_BIAS_0 {-26, -42, 71}

#define TENSOR_DENSE_BIAS_0_DEC_BITS {12}

#define DENSE_BIAS_LSHIFT {1}

#define DENSE_OUTPUT_RSHIFT {8}


/* output q format for each layer */
#define INPUT_1_OUTPUT_DEC 4
#define INPUT_1_OUTPUT_OFFSET 0
#define CONV1D_OUTPUT_DEC 4
#define CONV1D_OUTPUT_OFFSET 0
#define LEAKY_RE_LU_OUTPUT_DEC 4
#define LEAKY_RE_LU_OUTPUT_OFFSET 0
#define CONV1D_1_OUTPUT_DEC 4
#define CONV1D_1_OUTPUT_OFFSET 0
#define LEAKY_RE_LU_1_OUTPUT_DEC 4
#define LEAKY_RE_LU_1_OUTPUT_OFFSET 0
#define FLATTEN_OUTPUT_DEC 4
#define FLATTEN_OUTPUT_OFFSET 0
#define DENSE_OUTPUT_DEC 5
#define DENSE_OUTPUT_OFFSET 0
#define DROPOUT_OUTPUT_DEC 5
#define DROPOUT_OUTPUT_OFFSET 0
#define SOFTMAX_OUTPUT_DEC 7
#define SOFTMAX_OUTPUT_OFFSET 0

/* bias shift and output shift for none-weighted layer */

/* tensors and configurations for each layer */
static int8_t nnom_input_data[450] = {0};

const nnom_shape_data_t tensor_input_1_dim[] = {150, 3};
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

const nnom_shape_data_t tensor_conv1d_kernel_0_dim[] = {3, 3, 30};
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

const nnom_shape_data_t tensor_dense_kernel_0_dim[] = {255, 3};
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

const nnom_shape_data_t tensor_dense_bias_0_dim[] = {3};
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
static int8_t nnom_output_data[3] = {0};

const nnom_shape_data_t tensor_output0_dim[] = {3};
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
