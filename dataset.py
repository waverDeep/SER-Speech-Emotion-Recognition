from torch.utils.data import Dataset
import glob
import os
import utils.features as features
import torchaudio
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split


def get_all_file_path(input_dir, file_extension='wav'):
    temp = glob.glob(os.path.join(input_dir, '**', '*.{}'.format(file_extension)), recursive=True)
    return temp

def get_filename(input_filepath):
    return input_filepath.split('/')[-1]

def get_pure_filename(input_filepath):
    temp = input_filepath.split('/')[-1]
    return temp.split('.')[0]

def get_ravdess_property(input_filepath):
    pure_filename = get_pure_filename(input_filepath)
    idea = pure_filename.split('-')
    # 03-01-01-01-01-01-01
    '''
    Modality (01 = full-AV, 02 = video-only, 03 = audio-only).
    Vocal channel (01 = speech, 02 = song).
    Emotion (01 = neutral, 02 = calm, 03 = happy, 04 = sad, 05 = angry, 06 = fearful, 07 = disgust, 08 = surprised).
    Emotional intensity (01 = normal, 02 = strong). NOTE: There is no strong intensity for the 'neutral' emotion.
    Statement (01 = "Kids are talking by the door", 02 = "Dogs are sitting by the door").
    Repetition (01 = 1st repetition, 02 = 2nd repetition).
    Actor (01 to 24. Odd numbered actors are male, even numbered actors are female).
    '''
    return {'Modality': idea[0], 'VocalChannel': idea[1], 'Emotion': idea[2], 'EmotionalIntensity': idea[3],
            'Statement': idea[4], 'Repetition': idea[5], 'Actor': idea[6]}

def manipulate_audio_duration(source, sr, audio_duration):
    audio_length = len(source[0])
    input_length = int(round(audio_duration * sr))
    if audio_length > input_length: # cut out
        mani_source = source[0, :input_length]
        mani_source = torch.reshape(mani_source, (1, input_length))
    elif audio_length < input_length: # padd
        mani_source = nn.ConstantPad1d((0, input_length - audio_length), 0)(source)
    else:
        mani_source = source

    return mani_source, sr

class AudioDatasetType01(Dataset):
    def __init__(self, input_file_list, feature_config):
        self.file_list = input_file_list
        self.feature_config = feature_config

    def __getitem__(self, index):
        filepath = self.file_list[index]
        source, sr = torchaudio.load(filepath)
        if self.feature_config['audio_duration'] is not None:
            source, sr = manipulate_audio_duration(source, sr, self.feature_config['audio_duration'])
        waveform = 0
        if self.feature_config['spectrogram_type'] == 'spectrogram':
            waveform = features.extract_spectrogram(source=source,
                                                    sample_rate=sr,
                                                    n_fft=self.feature_config['n_fft'],
                                                    window_size=self.feature_config['window_size'],
                                                    window_stride=self.feature_config['window_stride'])
        elif self.feature_config['spectrogram_type'] == 'melspectrogram':
            waveform = features.extract_mel_spectrogram(source=source,
                                                        sample_rate=sr,
                                                        n_mels=self.feature_config['n_mels'],
                                                        n_fft=self.feature_config['n_fft'],
                                                        window_size=self.feature_config['window_size'],
                                                        window_stride=self.feature_config['window_stride'])

        label = get_ravdess_property(filepath)
        label = label['Emotion']

        return waveform, label

    def __len__(self):
        return len(self.file_list)

# simple hold out validation
def unweighted_split_train_test_file_list(input_dir, file_extension='wav', test_size=0.2, random_state=42):
    file_list = get_all_file_path(input_dir, file_extension)
    train_dataset, test_dataset = train_test_split(file_list, test_size=test_size, random_state=random_state)
    valid_dataset = test_dataset[:int(round(len(test_dataset)/2))]
    test_dataset = test_dataset[int(round(len(test_dataset)/2)):]
    return train_dataset, valid_dataset, test_dataset

# simple hold out validation
def weighted_split_train_test_file_list(input_dir, file_extension='wav', test_size=0.2, random_state=42):
    pass