from base import Method
import pandas as pd
import numpy as np
import os
from datetime import datetime
import nopy
from numpy import VisibleDeprecationWarning
import warnings
warnings.filterwarnings(action="ignore", category=VisibleDeprecationWarning)
warnings.filterwarnings(action="ignore", category=RuntimeWarning)


class Complete_geo(Method):
    def __init__(self, data: pd.DataFrame, path_save: str, test_start: int) -> None:
        super().__init__(data, path_save)
        self.test_start = test_start
        self.alpha = 0.01
    

    def fill_operand(self, formula, struct, idx, temp_0, temp_op, temp_1, target, mode, add_sub_done, mul_div_done):
        if mode == 0: # Sinh dấu cộng trừ đầu mỗi cụm
            # Tìm idx cụm
            gr_idx = list(struct[:,2]-1).index(idx)

            start = 0
            if (formula[0:idx] == self.last_formula[0:idx]).all():
                start = self.last_formula[idx]

            for op in range(start, 2):
                new_formula = formula.copy()
                new_struct = struct.copy()
                new_formula[idx] = op
                new_struct[gr_idx,0] = op
                if op == 1:
                    new_add_sub_done = True
                    new_formula[new_struct[gr_idx+1:,2]-1] = 1
                    new_struct[gr_idx+1:,0] = 1
                else:
                    new_add_sub_done = False

                if self.fill_operand(new_formula, new_struct, idx+1, temp_0, temp_op, temp_1, target, 1, new_add_sub_done, mul_div_done):
                    return True

        elif mode == 1:
            start = 0
            if (formula[0:idx] == self.last_formula[0:idx]).all():
                start = self.last_formula[idx]

            valid_operand = nopy.get_valid_operand(formula, struct, idx, start, self.OPERAND.shape[0])
            if valid_operand.shape[0] > 0:
                if formula[idx-1] < 2:
                    temp_op_new = formula[idx-1]
                    temp_1_new = self.OPERAND[valid_operand].copy()
                else:
                    temp_op_new = temp_op
                    if formula[idx-1] == 2:
                        temp_1_new = temp_1 * self.OPERAND[valid_operand]
                    else:
                        temp_1_new = temp_1 / self.OPERAND[valid_operand]

                if idx + 1 == formula.shape[0] or (idx+2) in struct[:,2]:
                    if temp_op_new == 0:
                        temp_0_new = temp_0 + temp_1_new
                    else:
                        temp_0_new = temp_0 - temp_1_new
                else:
                    temp_0_new = np.array([temp_0]*valid_operand.shape[0])

                if idx + 1 == formula.shape[0]:
                    temp_0_new[np.isnan(temp_0_new)] = -1.7976931348623157e+308
                    temp_0_new[np.isinf(temp_0_new)] = -1.7976931348623157e+308
                    # valid_idx, check_target = nopy.get_valid_idxsss_and_targetsss(temp_0_new, self.PROFIT, self.INDEX, self.num_test, target, self.profit_method_index)
                    # if valid_idx.shape[0] > 0:
                    #     temp_list_formula = np.array([formula]*valid_idx.shape[0])
                    #     temp_list_formula[:,idx] = valid_operand[valid_idx]
                    #     x_1 = self.count[0]
                    #     x_2 = self.count[0] + valid_idx.shape[0]
                    #     self.list_formula[0][x_1:x_2] = temp_list_formula
                    #     self.list_formula[1][x_1:x_2] = check_target
                    #     self.count[0:3:2] += valid_idx.shape[0]

                    # self.last_formula[:] = formula[:]
                    # self.last_formula[idx] = self.OPERAND.shape[0]
                    # if self.count[0] >= self.count[1] or self.count[2] >= self.count[3]:
                    #     return True

                    for w_i in range(temp_0_new.shape[0]):
                        weight = temp_0_new[w_i]
                        values, indexes, profits = nopy.get_value_index_profit(weight, self.PROFIT, self.INDEX)
                        
                        for c_i in range(self.test_start, self.INDEX.shape[0]-1):
                            value = values[0:c_i]
                            index = indexes[0:c_i]
                            profit = profits[0:c_i]
                            geo, geo_L, value_geo_L = nopy.geo_geo_L_value_geo_L(value, index, profit, target)
                            if geo >= target and geo_L - geo >= self.alpha:
                                har, har_L, value_har_L = nopy.har_har_L_value_har_L(value, index, profit, 0.0)
                                temp_weight = weight[self.INDEX[-1-c_i]:self.INDEX[-1]]
                                temp_profit = self.PROFIT[self.INDEX[-1-c_i]:self.INDEX[-1]]
                                bit = nopy.get_bit_mean(temp_weight, temp_profit)
                                temp_formula = formula.copy()
                                temp_formula[idx] = valid_operand[w_i]
                                self.list_formula.append(temp_formula)
                                self.list_geo.append(geo)
                                self.list_geo_L.append(geo_L)
                                self.list_value_geo_L.append(value_geo_L)
                                self.list_har.append(har)
                                self.list_har_L.append(har_L)
                                self.list_value_har_L.append(value_har_L)
                                self.list_value.append(values[c_i])
                                self.list_bit.append(bit)
                                self.list_invest_index.append(indexes[c_i])
                                self.list_invest_profit.append(profits[c_i])
                                self.list_cycle.append(c_i)
                                self.count[0:3:2] += 1
                    
                    self.last_formula[:] = formula[:]
                    self.last_formula[idx] = self.OPERAND.shape[0]
                    if self.count[0] >= self.count[1] or self.count[2] >= self.count[3]:
                        return True


                else:
                    temp_list_formula = np.array([formula]*valid_operand.shape[0])
                    temp_list_formula[:,idx] = valid_operand
                    if idx + 2 in struct[:,2]:
                        if add_sub_done:
                            new_idx = idx + 2
                            new_mode = 1
                        else:
                            new_idx = idx + 1
                            new_mode = 0
                    else:
                        if mul_div_done:
                            new_idx = idx + 2
                            new_mode = 1
                        else:
                            new_idx = idx + 1
                            new_mode = 2

                    for i in range(valid_operand.shape[0]):
                        if self.fill_operand(temp_list_formula[i], struct, new_idx, temp_0_new[i], temp_op_new, temp_1_new[i], target, new_mode, add_sub_done, mul_div_done):
                            return True

        elif mode == 2:
            start = 2
            if (formula[0:idx] == self.last_formula[0:idx]).all():
                start = self.last_formula[idx]

            if start == 0:
                start = 2

            valid_op = nopy.get_valid_op(struct, idx, start)
            for op in valid_op:
                new_formula = formula.copy()
                new_struct = struct.copy()
                new_formula[idx] = op
                if op == 3:
                    new_mul_div_done = True
                    for i in range(idx+2, 2*new_struct[0,1]-1, 2):
                        new_formula[i] = 3

                    for i in range(1, new_struct.shape[0]):
                        for j in range(new_struct[0,1]-1):
                            new_formula[new_struct[i,2] + 2*j + 1] = new_formula[2+2*j]
                else:
                    new_struct[:,3] += 1
                    new_mul_div_done = False
                    if idx == 2*new_struct[0,1] - 2:
                        new_mul_div_done = True
                        for i in range(1, new_struct.shape[0]):
                            for j in range(new_struct[0,1]-1):
                                new_formula[new_struct[i,2] + 2*j + 1] = new_formula[2+2*j]

                if self.fill_operand(new_formula, new_struct, idx+1, temp_0, temp_op, temp_1, target, 1, add_sub_done, new_mul_div_done):
                    return True

        return False


    def generate_formula(self, target_profit=1.0, formula_file_size=1000000, target_num_formula=1000000000):
        try:
            temp = np.load(self.path+"history_new_many.npy", allow_pickle=True)
            self.history = temp
        except:
            self.history =  np.array([0, 0]), 0

        self.last_formula = self.history[0].copy()
        self.last_uoc_idx = self.history[1]

        self.count = np.array([0, formula_file_size, 0, target_num_formula])
        last_operand = self.last_formula.shape[0] // 2
        num_operand = last_operand - 1

        while True:
            num_operand += 1
            print("Đang chạy sinh công thức có số toán hạng là ", num_operand, ". . .")
            self.list_formula = []
            self.list_geo = []
            self.list_geo_L = []
            self.list_value_geo_L = []
            self.list_har = []
            self.list_har_L = []
            self.list_value_har_L = []
            self.list_value = []
            self.list_bit = []
            self.list_invest_index = []
            self.list_invest_profit = []
            self.list_cycle = []

            list_uoc_so = []
            for i in range(1, num_operand+1):
                if num_operand % i == 0:
                    list_uoc_so.append(i)

            start_uoc_idx = 0
            if num_operand == last_operand:
                start_uoc_idx = self.history[1]

            formula = np.full(num_operand*2, 0)
            for i in range(start_uoc_idx, len(list_uoc_so)):
                print("Số phần tử trong 1 cụm", list_uoc_so[i])
                struct = np.array([[0, list_uoc_so[i], 1+2*list_uoc_so[i]*j, 0] for j in range(num_operand//list_uoc_so[i])])
                if num_operand != last_operand or i != self.last_uoc_idx:
                    self.last_formula = formula.copy()
                    self.last_uoc_idx = i

                while self.fill_operand(formula, struct, 0, np.zeros(self.OPERAND.shape[1]), 0, np.zeros(self.OPERAND.shape[1]), target_profit, 0, False, False):
                    self.save_history()

            if self.save_history():
                break
    
    def save_history(self):
        np.save(self.path+"history_new_many.npy", (self.last_formula, self.last_uoc_idx))
        print("Đã lưu lịch sử.")
        if self.count[0] == 0:
            return False
        
        min_time = self.TRAINING_DATA["TIME"].min()
        df = pd.DataFrame({
            "formula": self.list_formula,
            "geomean": self.list_geo,
            "geo_limit": self.list_geo_L,
            "value_geo_limit": self.list_value_geo_L,
            "harmean": self.list_har,
            "har_limit": self.list_har_L,
            "value_har_limit": self.list_value_har_L,
            "value": self.list_value,
            "bitmean": self.list_bit,
            "invest": [self.TRAINING_DATA["SYMBOL"].iloc[i] for i in self.list_invest_index],
            "profit": self.list_invest_profit,
            "cycle": [min_time + i for i in self.list_cycle]
        })
        while True:
            pathSave = self.path + f"formula_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + ".csv"
            if not os.path.exists(pathSave):
                df.to_csv(pathSave, index=False)
                self.count[0] = 0
                self.list_formula = []
                self.list_geo = []
                self.list_geo_L = []
                self.list_value_geo_L = []
                self.list_har = []
                self.list_har_L = []
                self.list_value_har_L = []
                self.list_value = []
                self.list_bit = []
                self.list_invest_index = []
                self.list_invest_profit = []
                self.list_cycle = []
                print("Đã lưu công thức")
                if self.count[2] >= self.count[3]:
                    raise Exception("Đã sinh đủ công thức theo yêu cầu.")

                return False
            