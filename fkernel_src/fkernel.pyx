# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from cython.parallel import prange
from libc.math cimport atan2, log, exp, cos, sin

cpdef void mandelbrot_2(int[:, ::1] fba, int res_x, int res_y, int max_iter, double center_x, double center_y, double zoom) noexcept nogil:
    
    cdef int y
    cdef double z_real, z_imag, c_real, c_imag, temp_real
    cdef int x, i

    cdef double scale = 1.0 / (res_y * zoom)

    for y in prange(res_y, nogil=True, schedule='dynamic'):

        c_imag = center_y - (2.0 * y - res_y) * scale

        for x in range(res_x):

            c_real = center_x + (2.0 * x - res_x) * scale

            z_real = 0.0
            z_imag = 0.0

            fba[y, x] = max_iter

            for i in range(max_iter):
                temp_real =  z_real * z_real - z_imag * z_imag + c_real
                z_imag = 2.0 * z_real * z_imag + c_imag         
                z_real = temp_real

                if z_real * z_real + z_imag * z_imag > 4:
                    fba[y, x] = i
                    break

cdef inline void pow_c(double *z_real, double *z_imag, double w_real, double w_imag) noexcept nogil:

    cdef double zr = z_real[0]
    cdef double zi = z_imag[0]
    
    if zr == 0.0 and zi == 0.0:
        if w_real == 0.0 and w_imag == 0.0:
            z_real[0] = 1.0
            z_imag[0] = 0.0
        else:
            z_real[0] = 0.0
            z_imag[0] = 0.0
        return

    cdef double ln_abs_z = log(zr * zr + zi * zi) / 2
    cdef double phi = atan2(zi, zr)

    cdef double pow_e = w_real * ln_abs_z - w_imag * phi
    cdef double theta = w_imag * ln_abs_z + w_real * phi

    z_real[0] = exp(pow_e) * cos(theta)
    z_imag[0] = exp(pow_e) * sin(theta)

# cpdef void mandelbrot_comp(int[:, :] fba, int res_x, int res_y, int max_iter, double center_x, double center_y, double zoom, double w_real, double w_imag):