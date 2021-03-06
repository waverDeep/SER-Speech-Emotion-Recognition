import torch
import old.load_dataset.data_split_functions as data_split_functions
import multiprocessing
import old.load_dataset.AudioDataset as AudioDataset
from torch.utils.data import DataLoader
from old.models.model import Vanilla_CNN
from old.functions import optimizers, losses
import warnings
warnings.filterwarnings('ignore')

def load_dataset(root_dir, file_extension='wav', batch_size=32):

    # 2. split train, test dataset
    train_filelist, test_filelist = data_split_functions.split_train_test_file_list(root_dir=root_dir,
                                                                                    file_extension=file_extension)

    train_dataset = AudioDataset.AudioDataset(dataset=train_filelist)
    test_dataset = AudioDataset.AudioDataset(dataset=test_filelist)

    train_dataloader = DataLoader(train_dataset, batch_size=batch_size,
                                  shuffle=True,
                                  num_workers=multiprocessing.cpu_count())
    test_dataloader = DataLoader(test_dataset, batch_size=batch_size,
                                 shuffle=False,
                                 num_workers=multiprocessing.cpu_count())

    return train_dataloader, test_dataloader


def train(epoch, network, dataloader, device, loss_func, optimizer_func):
    network.train()
    for e in range(epoch):
        running_loss = 0.0
        running_corrects = 0

        for batch_idx, (inputs, targets) in enumerate(dataloader):
            inputs = torch.FloatTensor(inputs)
            inputs = inputs.to(device)
            targets = targets.to(device)
            optimizer_func.zero_grad()
            outputs = network(inputs)
            _, preds = torch.max(outputs, 1)
            loss = loss_func(outputs, targets)
            loss.backward()
            optimizer_func.step()

            running_loss += loss.item()
            running_corrects += torch.sum(preds == targets.data)
            if batch_idx % 20 == 19:  # print every 2000 mini-batches
                print('[%d, %5d] loss: %.3f' %
                      (epoch + 1, batch_idx + 1, running_loss / 2000))
                running_loss = 0.0
        epoch_acc = running_corrects.double() / len(dataloader.dataset)
        print("{}epoch : acc : {}".format(e, epoch_acc))

    print('Finish Training...')


def test(network, dataloader, device, loss_func):
    test_loss = 0
    total = 0
    correct = 0

    with torch.no_grad():
        for batch_idx, (inputs, targets) in enumerate(dataloader):
            inputs = torch.FloatTensor(inputs)
            inputs, targets = inputs.to(device), targets.to(device)

            outputs = network(inputs)
            loss = loss_func(outputs, targets)

            test_loss += loss.item()

            _, predicted = torch.max(outputs.data, 1)
            total += targets.size(0)
            correct += (predicted == targets).sum().item()

        print('Accuracy of the network by test images: %d %%' % (
                100 * correct / total))
        print('loss : %d' % test_loss)



def main():
    root_dir = '../dataset_resample'
    file_extension = 'wav'
    batch_size = 128
    epoch = 40

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    train_dataloader, test_dataloader = load_dataset(root_dir=root_dir,
                                                     file_extension=file_extension,
                                                     batch_size=batch_size)

    network = Vanilla_CNN()
    network = network.to(device)

    loss = losses.choose_loss('CrossEntropyLoss')
    optimizer = optimizers.choose_optimizer('SGD', network, lr=0.001, momentum=0.9, weight_decay=0.1)

    train(epoch, network, train_dataloader, device, loss_func=loss, optimizer_func=optimizer)
    test(network, dataloader=test_dataloader, device=device, loss_func=loss)

main()







