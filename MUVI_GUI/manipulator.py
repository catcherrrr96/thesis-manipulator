"""
@author: Jason Grillo
"""
# import quaternions as q
import math as m

class MUVI_manipulator:
    def __init__(self, x_stage, z_stage, y_stage, p_stage):
        self.x_stage = x_stage
        self.z_stage = z_stage
        self.y_stage = y_stage
        self.p_stage = p_stage

        self.theta = 0
        self.psi = 0

        self.MOVING = False
        # Define Coordinate System
        self.unitx = [1,0,0]
        self.unity = [0,1,0]
        self.unitz = [0,0,1]
        # Define Ray Intersection Point Behind Iris
        self.iris_D = 5.8       # mm
        self.FOV = 30*m.pi/180  # rad
        self.l_focus = self.iris_D/(2*m.tan(self.FOV/2))   # mm
        # Define Mirror and Laser Quaternions
        self.r_bot1 = [0, -12.7, 20.882, 2.312]
        self.r_bot2 = [0, 0, 11.901, -6.669]
        self.r_bot3 = [0, 12.7, 20.882, 2.312]
        self.r_top4 = [0, -25.4, 23.324, 37.204]
        self.r_top5 = [0, 0, 5.364, 19.244]
        self.r_top6 = [0, 25.4, 23.324, 37.204]
        self.beam1 = [0, 0, 80, 32.45]
        self.beam2 = [0, 0, 18.57, 32.45]
        # Initialize Rotation Variables
        self.r_bot1_prime = [0, 0, 0, 0]
        self.r_bot2_prime = [0, 0, 0, 0]
        self.r_bot3_prime = [0, 0, 0, 0]
        self.r_top4_prime = [0, 0, 0, 0]
        self.r_top5_prime = [0, 0, 0, 0]
        self.r_top6_prime = [0, 0, 0, 0]
        self.top_mirror_norm = [0, 0, 0, 0]
        self.bot_mirror_norm = [0, 0, 0, 0]
        self.top_ints_pt = [0, 0, 0, 0]
        self.bot_ints_pt = [0, 0, 0, 0]
        self.beam_top_refl = [0, 0, 0, 0]
        self.beam_bot_refl = [0, 0, 0, 0]

    def set_angle(self):
        self.psi = self.y_stage.get_true_position()
        self.theta = self.p_stage.get_true_position()

    def set_instrument_params(self, param_list):
        self.iris_D = float(param_list[0])
        self.FOV = float(param_list[1])*m.pi/180
        for quaternion in range(4):
            self.r_bot1[quaternion] = float(param_list[2][quaternion])
            self.r_bot2[quaternion] = float(param_list[3][quaternion])
            self.r_bot3[quaternion] = float(param_list[4][quaternion])
            self.r_top4[quaternion] = float(param_list[5][quaternion])
            self.r_top5[quaternion] = float(param_list[6][quaternion])
            self.r_top6[quaternion] = float(param_list[7][quaternion])
            self.beam1[quaternion] = float(param_list[8][quaternion])
            self.beam2[quaternion] = float(param_list[9][quaternion])
        self.l_focus = self.iris_D/(2*m.tan(self.FOV/2))

    # def set_instrument_quaternions(self, quaternions):

    def get_point_targets(self, theta_targ, psi_targ):
        if psi_targ > 0:
            x_mm = self.calc_rotation('YAW',psi_targ)
        else:
            x_mm = -self.calc_rotation('YAW',psi_targ)
        if theta_targ > 0:
            z_mm = self.calc_rotation('PITCH',theta_targ)
        else:
            z_mm = -self.calc_rotation('PITCH',theta_targ)
        y_deg = psi_targ
        p_deg = theta_targ
        return round(x_mm,4), round(z_mm,4), round(y_deg,4), round(p_deg,4)

    def get_current_psi(self):
        return self.psi

    def get_current_theta(self):
        return self.theta

    def calc_rotation(self, rotation, deg):
        rad = deg*m.pi/180
        if rotation == 'PITCH':
            q = [m.cos(rad/2), self.unitx[0]*m.sin(rad/2), self.unitx[1]*m.sin(rad/2), self.unitx[2]*m.sin(rad/2)]
            q_star = [m.cos(rad/2), -self.unitx[0]*m.sin(rad/2), -self.unitx[1]*m.sin(rad/2), -self.unitx[2]*m.sin(rad/2)]
        else:
            q = [m.cos(rad/2), self.unitz[0]*m.sin(rad/2), self.unitz[1]*m.sin(rad/2), self.unitz[2]*m.sin(rad/2)]
            q_star = [m.cos(rad/2), -self.unitz[0]*m.sin(rad/2), -self.unitz[1]*m.sin(rad/2), -self.unitz[2]*m.sin(rad/2)]
        self.r_bot1_prime = self.quatmultiply(self.quatmultiply(q,self.r_bot1),q_star)
        self.r_bot2_prime = self.quatmultiply(self.quatmultiply(q,self.r_bot2),q_star)
        self.r_bot3_prime = self.quatmultiply(self.quatmultiply(q,self.r_bot3),q_star)
        self.r_top4_prime = self.quatmultiply(self.quatmultiply(q,self.r_top4),q_star)
        self.r_top5_prime = self.quatmultiply(self.quatmultiply(q,self.r_top5),q_star)
        self.r_top6_prime = self.quatmultiply(self.quatmultiply(q,self.r_top6),q_star)
        self.bot_mirror_norm = self.cross(self.sub(self.r_bot1_prime[1::],self.r_bot2_prime[1::]),self.sub(self.r_bot3_prime[1::],self.r_bot2_prime[1::]))
        self.top_mirror_norm = self.cross(self.sub(self.r_top4_prime[1::],self.r_top5_prime[1::]),self.sub(self.r_top6_prime[1::],self.r_top5_prime[1::]))
        self.bot_mirror_norm = self.normalize(self.bot_mirror_norm)
        self.top_mirror_norm = self.normalize(self.top_mirror_norm)
        self.top_ints_pt, self.beam_top_refl = self.calc_beam_refl('top')
        self.bot_ints_pt, self.beam_bot_refl = self.calc_beam_refl('bot')
        if rotation == 'PITCH':
            trans_comp = abs(self.bot_ints_pt[2]) + abs(self.l_focus*m.sin(rad))
        else:
            trans_comp = abs(self.bot_ints_pt[0]) + abs(self.l_focus*m.sin(rad))
        return trans_comp

    def calc_beam_refl(self,mirror):
        if mirror == 'top':
            norm = self.top_mirror_norm
            P0 = self.beam1[1::]
            P1 = self.beam2[1::]
            P2 = self.r_top4_prime[1::]
        else:
            norm = self.bot_mirror_norm
            P0 = self.top_ints_pt
            P1 = self.add(self.top_ints_pt,self.beam_top_refl[1::])
            P2 = self.r_bot1_prime[1::]
        t = (norm[0]*P0[0]-norm[0]*P2[0] + norm[1]*P0[1]-norm[1]*P2[1] + norm[2]*P0[2]-norm[2]*P2[2])/(norm[0]*P0[0]-norm[0]*P1[0]+norm[1]*P0[1]-norm[1]*P1[1]+norm[2]*P0[2]-norm[2]*P1[2])
        ints_pt = [P0[0]+t*(P1[0]-P0[0]), P0[1]+t*(P1[1]-P0[1]), P0[2]+t*(P1[2]-P0[2])]
        reflection = self.sub([0, 0, 0, 0],self.quatmultiply(self.quatmultiply(self.make_quat(norm),self.sub(self.make_quat(P0),self.make_quat(P1))),self.make_quat(norm)))
        return ints_pt, reflection

    def sub(self, A, B):
        return [a - b for a, b in zip(A, B)]

    def add(self, A, B):
        return [a + b for a, b in zip(A, B)]

    def mag(self, x):
        # https://stackoverflow.com/questions/9171158/how-do-you-get-the-magnitude-of-a-vector-in-numpy
        return m.sqrt(sum(i**2 for i in x))

    def cross(self, a, b):
        # https://stackoverflow.com/questions/1984799/cross-product-of-two-vectors-in-python
        c = [a[1]*b[2] - a[2]*b[1],
             a[2]*b[0] - a[0]*b[2],
             a[0]*b[1] - a[1]*b[0]]
        return c

    def dot(self, a, b):
        # https://stackoverflow.com/questions/35208160/dot-product-in-python-without-numpy
        return sum(x*y for x,y in zip(a,b))

    def quatmultiply(self, p,q):
        scalar = p[0]*q[0] - self.dot(p[1::],q[1::])
        vi = p[0]*q[1] + q[0]*p[1] + self.cross(p[1::],q[1::])[0]
        vj = p[0]*q[2] + q[0]*p[2] + self.cross(p[1::],q[1::])[1]
        vk = p[0]*q[3] + q[0]*p[3] + self.cross(p[1::],q[1::])[2]
        return [scalar, vi, vj, vk]

    def make_quat(self, vector):
        return [0, vector[0], vector[1], vector[2]]

    def normalize(self, vector):
        magnitude = self.mag(vector)
        return [i/magnitude for i in vector]

# # For Testing Purposes:
# MUVI = MUVI_manipulator(1,1,1,1)
# print(MUVI.get_point_targets(15,-15))
