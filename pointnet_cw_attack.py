import torch

import torch.nn as nn

import torch.optim as optim



import copy
from torch.autograd import Variable






if torch.cuda.is_available():
  device = torch.device('cuda:0')
  print('running on GPU')
else:
  device = torch.device('cpu')
  print('running on CPU')


  class L2_CW(object):
    def __init__(self, c=2, k=0, max_iter=100, lr=1e-2):
      self.c = c
      self.k = k
      self.lr = lr
      self.max_iter = max_iter

    def calc_f(self, logits, target_index):
      batch_size = logits.shape[0]
      class_size = logits.shape[1]
      logits_t = torch.masked_select(logits, torch.eye(class_size)[target_index].bool())
      logits_index_sorted = logits.argsort(descending=True, dim=1)
      max_logit_index = torch.zeros(batch_size)
      for i in range(batch_size):
        max_logit_index[i] = logits_index_sorted[i][0 if logits_index_sorted[i][0] != target_index[i] else 1]
      max_logit = torch.masked_select(logits, torch.eye(class_size)[max_logit_index.long()].bool())

      f = torch.clamp(max_logit - logits_t, min=self.k)

      return f

    def init_attack(self, points, noise_var = 0.01):


      init_pert = torch.randn(points.shape) * noise_var

      return init_pert

    def loss_function(self, adv_points, points, out, targets):
      f = self.calc_f(out, targets).sum()
      l2_loss = nn.MSELoss(reduction='sum')(adv_points, points)

      loss = l2_loss + self.c * f
      return loss, l2_loss, f

    def attack(self, model, points, targets):

      original_points = copy.deepcopy(points)

      w = Variable(self.init_attack(original_points), requires_grad=True)
      adv_points = w + original_points

      optimizer = optim.Adam([w], lr=self.lr)
      for i in range(self.max_iter):
        optimizer.zero_grad()
        model.zero_grad()
        out, _, _ = model(adv_points)
        loss, l2, f = self.loss_function(adv_points, points, out, targets)
        loss.backward()
        optimizer.step()

        adv_points = w + original_points


        if i % 10 == 0:
          print('loss: ', loss.item(), 'mse: ', l2.item(), 'f: ', f.item())

      out, _, _ = model(adv_points)
      labels = torch.argmax(out, dim=1)
      return adv_points, labels
    def attack2(self, model, points, targets):

      original_points = copy.deepcopy(points)
      adv_points = original_points + self.init_attack(original_points)
      adv_points = Variable(adv_points, requires_grad=True)

      optimizer = optim.Adam([adv_points], lr=self.lr)
      for i in range(self.max_iter):
        optimizer.zero_grad()
        model.zero_grad()
        out, _, _ = model(adv_points)
        loss, l2, f = self.loss_function(adv_points, points, out, targets)
        loss.backward()
        optimizer.step()


        if i % 10 == 0:
          print('loss: ', loss.item(), 'mse: ', l2.item(), 'f: ', f.item())

      out, _, _ = model(adv_points)
      labels = torch.argmax(out, dim=1)
      return adv_points, labels







