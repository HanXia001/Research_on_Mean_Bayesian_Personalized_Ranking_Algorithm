import random
from collections import defaultdict
import numpy as np
from sklearn.metrics import roc_auc_score
import scores
from openpyxl import Workbook
from tqdm import tqdm

class MBPR:
    user_count = 15400
    item_count = 1000
    latent_factors = 20
    lr = 0.01
    reg = 0.01
    train_count = 1000
    train_data_path = "ydata-ymusic-rating-study-v1_0-train.txt"
    test_data_path = "ydata-ymusic-rating-study-v1_0-test.txt"
    size_u_i = user_count * item_count
    # latent_factors of U & V
    U = np.random.rand(user_count, latent_factors) * 0.01
    np.savetxt("U.txt",U)

    V = np.random.rand(item_count, latent_factors) * 0.01
    np.savetxt("V.txt",V)

    biasV = np.random.rand(item_count) * 0.01
    np.savetxt("biasV.txt",biasV)

    test_data = np.zeros((user_count, item_count))
    test = np.zeros(size_u_i)
    predict_ = np.zeros(size_u_i)

    def get_mean_rating(self,path):
        u_i_r = np.zeros((self.user_count+1,self.item_count+1))
        with open(path,"r") as f:
            for line in f.readlines():
                u, i, r = line.split("	")
                u = int(u)
                i = int(i)
                r = int(r)
                u_i_r[u][i] = r
        u_mean_rating = {}
        for u in range(self.user_count+1):
            if u == 0:
                continue
            num = 0
            for i in range(self.item_count+1):
                if i ==0:
                    continue
                if u_i_r[u][i] != 0:
                    num += 1
                    continue
            u_mean_rating[u] = sum(u_i_r[u])/num
        return u_i_r,u_mean_rating

    def load_data_(self, path_1, path_2):
        user_ratings = defaultdict(set)
        u_i_r_t ={} # {(u_i_r):t}
        max_u_id = -1
        max_i_id = -1
        u_i_r = {} # {(u,i):r}
        with open(path_1, 'r') as f:
            for line in f.readlines():
                u, i, r = line.split("	")
                u = int(u)
                i = int(i)
                r = int(r)
                # t = int(t)
                u_i_r_t[(u,i,r)] = 0
                u_i_r[(u,i)] = r
                user_ratings[u].add(i)
                max_u_id = max(u, max_u_id)
                max_i_id = max(i, max_i_id)
        with open(path_2, 'r') as f:
            for line in f.readlines():
                u, i, r = line.split("	")
                u = int(u)
                i = int(i)
                r = int(r)
                # t = int(t)
                u_i_r_t[(u,i,r)] = 0
                u_i_r[(u,i)] = r
                user_ratings[u].add(i)
                max_u_id = max(u, max_u_id)
                max_i_id = max(i, max_i_id)
        self.user_count = max_u_id
        self.item_count = max_i_id
        self.size_u_i = self.user_count * self.item_count
        self.test_data = np.zeros((self.user_count, self.item_count))
        self.test = np.zeros(self.size_u_i)
        self.predict_ = np.zeros(self.size_u_i)
        print("user_count:",self.user_count,"item_count:",self.item_count)

        _,u_mean_rating = self.get_mean_rating(path=path_1)
        train_over_mean = []
        test_lower_mean = []
        # print(u_i_r_t)
        for line in u_i_r_t.keys():
            if line[2] >= u_mean_rating[line[0]]:
                train_over_mean.append((line,u_i_r_t[line]))
            else:
                test_lower_mean.append((line,u_i_r_t[line]))
        with open("train_over_mean.txt","w+") as f:
            for i in train_over_mean:
                f.write(str(i[0][0]) + "\t" + str(i[0][1]) + "\t" + str(i[0][2]) + "\t" + str(i[1]) + "\n")
        with open("test_lower_mean.txt","w+") as f:
            for i in test_lower_mean:
                f.write(str(i[0][0]) + "\t" + str(i[0][1]) + "\t" + str(i[0][2]) + "\t" + str(i[1]) + "\n")
        return  'train_over_mean.txt','test_lower_mean.txt'

    def load_data(self, path):
        user_ratings = defaultdict(set)
        max_u_id = -1
        max_i_id = -1
        with open(path, 'r') as f:
            for line in f.readlines():
                u, i, r, t = line.split("	")
                u = int(u)
                i = int(i)
                user_ratings[u].add(i)
                max_u_id = max(u, max_u_id)
                max_i_id = max(i, max_i_id)
        return user_ratings

    def load_test_data(self, path):
        file = open(path, 'r')
        for line in file:
            line = line.split('	')
            user = int(line[0])
            item = int(line[1])
            self.test_data[user - 1][item - 1] = 1

    def train(self, user_ratings_train,noise=None):
        for user in range(self.user_count):
            # sample a user
            u = random.randint(1, self.user_count)
            if u not in user_ratings_train.keys():
                continue
            # sample a positive item from the observed items
            i = random.sample(user_ratings_train[u], 1)[0]
            # sample a negative item from the unobserved items
            j = random.randint(1, self.item_count)
            while j in user_ratings_train[u]:
                j = random.randint(1, self.item_count)
            u -= 1
            i -= 1
            j -= 1
            r_ui = np.dot(self.U[u], self.V[i].T) + self.biasV[i]
            r_uj = np.dot(self.U[u], self.V[j].T) + self.biasV[j]
            r_uij = r_ui - r_uj

            loss_func = -1.0 / (1 + np.exp(r_uij))
            # update U and V
            self.U[u] += -self.lr * (loss_func * (self.V[i] - self.V[j]) + self.reg * self.U[u])
            self.V[i] += -self.lr * (loss_func * self.U[u] + self.reg * self.V[i])
            self.V[j] += -self.lr * (loss_func * (-self.U[u]) + self.reg * self.V[j])
            # update biasV
            self.biasV[i] += -self.lr * (loss_func + self.reg * self.biasV[i])
            self.biasV[j] += -self.lr * (-loss_func + self.reg * self.biasV[j])

    def predict(self, user, item):
        predict = np.mat(user) * np.mat(item.T)
        return predict

    def main(self):
        user_ratings_train = self.load_data(self.train_data_path)
        self.load_test_data(self.test_data_path)
        tbar_1 = tqdm(total=self.user_count*self.item_count)
        for u in range(self.user_count):
            for item in range(self.item_count):
                tbar_1.update(1)
                if int(self.test_data[u][item]) == 1:
                    self.test[u * self.item_count + item] = 1
                else:
                    self.test[u * self.item_count + item] = 0
        # training
        tbar_1.close()
        max_re_count = 30
        tbar_2 = tqdm(total=self.train_count*max_re_count)
        wb = Workbook()
        sheet = wb.active
        sheet.title = "New Shit"
        re_count = 3
        for t in range(max_re_count):
            for i in range(self.train_count):
                tbar_2.update(1)
                self.train(user_ratings_train,noise=0)

            predict_matrix = self.predict(self.U, self.V)

            # prediction
            self.predict_ = predict_matrix.getA().reshape(-1)
            self.predict_ = pre_handel(user_ratings_train, self.predict_, self.item_count)
            auc_score = roc_auc_score(self.test, self.predict_)
            print('AUC:', auc_score)
            # Top-K evaluation
            MAP,MRR,Prec,Rec,F1,NDCG,l_call = scores.topK_scores(self.test, self.predict_, re_count, self.user_count, self.item_count)
            sheet["A%d" % (t+1)].value = re_count
            sheet["B%d" % (t+1)].value = auc_score
            sheet["C%d" % (t+1)].value = MAP
            sheet["D%d" % (t+1)].value = MRR
            sheet["E%d" % (t+1)].value = Prec
            sheet["F%d" % (t+1)].value = Rec
            sheet["G%d" % (t+1)].value = F1
            sheet["H%d" % (t+1)].value = NDCG
            sheet["I%d" % (t+1)].value = l_call
            if re_count > 30:
                break
            re_count += 1
            self.U = np.loadtxt("U.txt")
            self.V = np.loadtxt("V.txt")
            self.biasV = np.loadtxt("biasV.txt")
        wb.save("MBPR各评价标准.xlsx")
        wb.close()
        tbar_2.close()

def pre_handel(set, predict, item_count):
    # Ensure the recommendation cannot be positive items in the training set.
    for u in set.keys():
        for j in set[u]:
            predict[(u - 1) * item_count + j - 1] = 0
    return predict

if __name__ == '__main__':
    mbpr = MBPR()
    mbpr.train_data_path,mbpr.test_data_path = mbpr.load_data_(mbpr.train_data_path,mbpr.test_data_path)
    mbpr.main()