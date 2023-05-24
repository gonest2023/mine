import pyautogui
from pywinauto import Application
import time,random
import numpy as np

class Mine():

    shape = {
        1:{
            'h':8,
            'w':8,
            'pic':'./pic/chuji.png'
        },
        3: {
            'h': 16,
            'w': 30,
            'pic': './pic/gaoji.png'
        }
    }

    color_map = {
        (0, 0, 255): 1,
        (0, 128, 0): 2,
        (255, 0, 0): 3,
        (0, 0, 128): 4,
        (128, 0, 0): 5,
        (0, 128, 128): 6,
        (0, 0, 0): 7,
        (128, 128, 128): 81,
        (192, 192, 192): -1,
        (7, 7, 7): -3
    }

    def __init__(self,level=3):
        self.app = Application(backend='uia')
        self.level = level
        self.h = self.shape[level]['h']
        self.w = self.shape[level]['w']

    def start(self):
        self.app.start('./arbiter/ms_arbiter.exe')
        time.sleep(0.5)
        self.mine = self.app['Minesweeper Arbiter']
        time.sleep(0.5)
        self.mine.set_focus()
        time.sleep(0.5)
        self.select_level()

    def start_do(self):
        self.get_game_zone()
        self.get_pos()
        self.nn = np.ones((self.h,self.w)) * -1
        self.grids = self.h * self.w

    def select_level(self):
        pyautogui.press(str(self.level))

    def get_game_zone(self):
        self.game_zone = pyautogui.locateOnScreen(self.shape[self.level]['pic'],confidence=0.99)
        self.region = (
            self.game_zone.left,
            self.game_zone.top,
            (self.game_zone.left + self.game_zone.width),
            (self.game_zone.top + self.game_zone.height)
        )

    def get_pos(self):
        x = [(4+10 + 20*i) for i in range(self.w)]
        y = [(4 + 10 + 20 * i) for i in range(self.h)]
        self.local_X = np.repeat(x, self.h).reshape(self.w, self.h).T
        self.local_Y = np.repeat(y, self.w).reshape(self.h, self.w)
        self.X = self.local_X + self.game_zone.left
        self.Y = self.local_Y + self.game_zone.top
        # print(x,y)

    def random_click(self):
        x = random.randint(0, self.shape[self.level]['h'] - 1)
        y = random.randint(0, self.shape[self.level]['w'] - 1)
        if self.nn[x, y] != -1:
            self.random_click()
        pyautogui.click(x=self.X[x, y], y=self.Y[x, y])
        self.grids = self.grids - 1

        self.get_num()
        if len(self.nn[self.nn == 9]) > 0:
            time.sleep(0.5)
            pyautogui.click(x=self.X[0, 4] - 10, y=self.Y[0, 4] - 40)
            self.start_do()
            self.random_click()
        if len(self.nn[self.nn == -1]) == self.grids:
            self.random_click()

    def get_num(self):
        game_image = pyautogui.screenshot(region=self.region)
        index = np.argwhere(self.nn == -1)
        for i in index:
            index_x = i[0]
            index_y = i[1]
            x_pos = self.local_X[index_x, index_y]
            y_pos = self.local_Y[index_x, index_y]
            color = game_image.getpixel((x_pos, y_pos))
            color = tuple([self.my_round(x) for x in color])
            if color not in self.color_map.keys():
                color = (7, 7, 7)
            num = self.color_map[color]
            if num == -1:
                c = game_image.getpixel((x_pos + 8, y_pos))
                c = tuple([self.my_round(x) for x in c])
                if c == (192, 192, 192):
                    num = 0
            elif num == 7:
                c = game_image.getpixel((x_pos - 3, y_pos))
                c = tuple([self.my_round(x) for x in c])
                if c == (0, 0, 0):
                    num = 9
            elif num == 81:
                c = game_image.getpixel((x_pos + 3, y_pos))
                c = tuple([self.my_round(x) for x in c])
                if c == (0, 0, 0):
                    num = 9
                elif c == (0, 128, 0):
                    num = 2

            if num > 9:
                c = game_image.getpixel((x_pos + 2, y_pos))
                c = tuple([self.my_round(x) for x in c])
                if c == (0, 128, 0):
                    num = 2

            self.nn[index_x, index_y] = num

    def my_round(self, x):
        if x < 10:
            x = 0
        elif x < 138:
            x = 128
        elif x > 245:
            x = 255
        return x

    def get_around(self, nn, x, y):
        nn_ = nn[x - 1:x + 2, y - 1:y + 2]
        return nn_

    def padnn(self, nn):
        nn_ = np.pad(nn, 1).copy()
        return nn_

    def mark_mine(self, nn):
        self.pro_nn = np.ones((self.h + 2, self.w + 2, 8, 6)) * -1

        index = np.argwhere(self.pad_nn > 0)
        for i in index:
            x = i[0]
            y = i[1]
            nn_ = self.get_around(self.pad_nn, x, y)
            count_1 = np.int64(nn_ == -1).sum()
            count_2 = np.int64(nn_ == -2).sum()
            count = nn_[1, 1] - count_2

            if count_1 > 0:
                nn_index = np.argwhere(nn_ == -1)
                for ii in nn_index:
                    x_ii = x - 1 + ii[0]
                    y_ii = y - 1 + ii[1]
                    self.mark_P(x_ii, y_ii, [x_ii, y_ii, x, y, count, count_1])

    def mark_P(self, x, y, n_):
        n_p = self.pro_nn[x, y]
        n_p_ = n_p[n_p[:, 0] == -1]
        index = 8 - len(n_p_)
        n_p[index] = n_

    def simple_sovle(self):
        tmp_nn = self.pro_nn[self.pro_nn[..., -1] != -1]
        tmp_nn = tmp_nn[tmp_nn[..., -1] == tmp_nn[..., -2]]
        index_tmp_nn = tmp_nn[..., :2]
        index_tmp_nn = np.unique(index_tmp_nn, axis=0)
        for i in index_tmp_nn:
            print(i)
            x = int(i[0])
            y = int(i[1])
            self.pad_nn[x, y] = -2
            self.right(x, y)

    def exclude(self):
        tmp_nn = self.pro_nn[self.pro_nn[..., -2] == 0]
        index_tmp_nn = tmp_nn[..., 2:4]
        index_tmp_nn = np.unique(index_tmp_nn, axis=0)
        for i in index_tmp_nn:
            x = int(i[0])
            y = int(i[1])
            self.middle(x, y)

    def right(self, x, y):
        x_, y_ = self.get_xy(x, y)
        pyautogui.click(button='right', x=x_, y=y_)

    def middle(self, x, y):
        x_, y_ = self.get_xy(x, y)
        pyautogui.click(button='middle', x=x_, y=y_)

    def left(self, x, y):
        x_, y_ = self.get_xy(x, y)
        pyautogui.click(button='left', x=x_, y=y_)

    def get_xy(self, x, y):
        x_ = self.X[x - 1, y - 1]
        y_ = self.Y[x - 1, y - 1]
        return x_, y_

    def get_pro_around(self, x, y):
        tmp_nn = self.get_around(self.pro_nn, x, y)
        tmp_nn = tmp_nn[tmp_nn[..., -1] != -1]
        if len(tmp_nn) == 0:
            tmp_nn = []
            tmp_nn_total = []
            tmp_nn_center = []
            tmp_nn_other = []
            tmp_nn_con = []
            c_num = 0
            return tmp_nn, tmp_nn_total, tmp_nn_center, tmp_nn_other, tmp_nn_con, c_num
        tmp_nn_total = np.unique(tmp_nn[..., :2], axis=0)
        tmp_nn_center = tmp_nn[(tmp_nn[..., 2] == x) & (tmp_nn[..., 3] == y)]
        c_num = tmp_nn_center[0, -2]
        tmp_nn_other = tmp_nn[~((tmp_nn[..., 2] == x) & (tmp_nn[..., 3] == y))]
        tmp_nn_other_ = tmp_nn_other[:, 2:]
        tmp_nn_con = np.unique(tmp_nn_other_, axis=0, return_counts=True)
        tmp_nn_con = np.column_stack((tmp_nn_con[1], tmp_nn_con[0]))

        return tmp_nn, tmp_nn_total, tmp_nn_center, tmp_nn_other, tmp_nn_con, c_num

    def get_max_min(self, tmp_nn_con):
        min_nn = tmp_nn_con[:, 0] - tmp_nn_con[:, -1] + tmp_nn_con[:, -2]
        min_nn[min_nn < 0] = 0
        max_nn = tmp_nn_con[:, 0].copy()
        count = tmp_nn_con[:, -2].copy()
        max_index = max_nn - count
        max_nn[max_index > 0] = count[max_index > 0]
        tmp_con_t = np.column_stack((max_nn, min_nn, tmp_nn_con))
        return tmp_con_t

    def complex_solve(self):
        index = np.argwhere(self.pad_nn > 0)

        for i_xy in index:
            x = int(i_xy[0])
            y = int(i_xy[1])
            #             x = 7
            #             y = 4
            tmp_nn, tmp_nn_total, tmp_nn_center, tmp_nn_other, tmp_nn_con, c_num = self.get_pro_around(x, y)
            #             print('tmp_nn',tmp_nn)
            #             print('tmp_nn_total',tmp_nn_total)
            #             print('tmp_nn_center',tmp_nn_center)
            #             print('tmp_nn_other',tmp_nn_other)
            #             print('tmp_nn_con',tmp_nn_con)
            #             print('c_num',c_num)
            if len(tmp_nn_center) == 0:
                continue

            tmp_con_m = self.get_max_min(tmp_nn_con)

            for i in tmp_con_m:
                #                 print(i,'-----')
                if i[2] == len(tmp_nn_center):
                    continue

                l_min = int(i[1])
                l_max = int(i[0]) + 1

                count_nn = tmp_nn[
                    (tmp_nn[..., -1] == i[-1]) & (tmp_nn[..., -2] == i[-2]) & (tmp_nn[..., -3] == i[-3]) & (
                                tmp_nn[..., -4] == i[-4])]
                tmp_nn_ = np.unique(count_nn[..., :2], axis=0)

                total_set = set([tuple(x) for x in tmp_nn_total])
                tmp_set = set([tuple(x) for x in tmp_nn_])

                other_set = total_set - tmp_set
                len_other = len(other_set)

                tmp_nn_center_ = tmp_nn_center[0, 2:]
                tmp_nn_center_ = np.insert(tmp_nn_center_, 0, len_other)
                tmp_nn_center_ = tmp_nn_center_.reshape(1, -1)
                tmp_nn_center_max_min = self.get_max_min(tmp_nn_center_)

                l_list = []
                r_list = []

                for t in tmp_nn_center_max_min:
                    r_min = int(t[1])
                    r_max = int(t[0]) + 1

                    for l in range(l_min, l_max):
                        for r in range(r_min, r_max):
                            if (l + r) == c_num:
                                l_list.append(l)
                                r_list.append(r)

                if len(l_list) == 1:
                    if l_list[0] == 0:
                        for tt in tmp_nn_:
                            xx = int(tt[0])
                            yy = int(tt[1])
                            self.left(xx, yy)
                    #                             self.pad_nn[xx,yy] = -4
                    elif l_list[0] == len(tmp_nn_):
                        for tt in tmp_nn_:
                            xx = int(tt[0])
                            yy = int(tt[1])
                            self.pad_nn[xx, yy] = -2
                            self.right(xx, yy)

                if len(r_list) == 1:
                    if r_list[0] == 0:
                        for tt in other_set:
                            xx = int(tt[0])
                            yy = int(tt[1])
                            self.left(xx, yy)
                    #                             self.pad_nn[xx,yy] = -4
                    elif r_list[0] == len(other_set):
                        for tt in other_set:
                            xx = int(tt[0])
                            yy = int(tt[1])
                            self.pad_nn[xx, yy] = -2
                            self.right(xx, yy)

    #                 print('other_set',other_set,l_min,l_max)
    #                 print('tmp_con_m',tmp_con_m)
    #             break

    def guess(self):
        ttmp = self.pro_nn[self.pro_nn[..., -1] != 1]
        ttmp_pro = ttmp[..., -2] / ttmp[..., -1]
        ttmp_pro = np.column_stack([ttmp, ttmp_pro])

        pro_dict = {}
        for i in range(len(ttmp_pro)):
            cur_key = f'{str(int(ttmp_pro[i, 0]))}-{str(int(ttmp_pro[i, 1]))}'
            cur_pro = ttmp_pro[i, -1]
            if cur_key in pro_dict.keys():
                if pro_dict[cur_key] < cur_pro:
                    pro_dict[cur_key] = cur_pro
            else:
                pro_dict[cur_key] = cur_pro

        min_index = min(pro_dict, key=pro_dict.get)
        xy = min_index.split('-')
        print(xy)
        x = int(xy[0])
        y = int(xy[1])
        print(x, y)
        self.left(x, y)

    def solve(self):
        self.start_do()
        self.random_click()
        while True:
            self.pre_nn = self.nn
            self.pad_nn = self.padnn(self.nn)
            self.mark_mine(self.pad_nn)
            self.simple_sovle()
            self.mark_mine(self.pad_nn)
            self.exclude()
            self.nn = self.pad_nn[1:-1, 1:-1]

            self.get_num()
            if len(self.pre_nn[self.pre_nn != self.nn]) == 0:
                self.complex_solve()
                self.get_num()
                if len(self.pre_nn[self.pre_nn != self.nn]) == 0:
                    print('guess')
                    if not len(self.nn[self.nn == -1]):
                        break
                    self.guess()
                    self.get_num()
                    if len(self.nn[self.nn == 9]) > 0:
                        time.sleep(0.5)
                        pyautogui.click(x=self.X[0, 4] - 10, y=self.Y[0, 4] - 40)
                        self.start_do()
                        self.random_click()



if __name__ == '__main__':
    m = Mine(3)
    m.start()
    time.sleep(5)
    m.solve()
