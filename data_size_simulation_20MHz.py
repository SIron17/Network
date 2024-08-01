
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

NUM_SIM = 3  # 시뮬레이션 반복 수
NUM_DTI = 10000  # 1번 시뮬레이션에서 수행될 Data Transmission Interval 수
USER_MAX = 500  # 사용자 수의 최댓값

# AP set
SIFS = 16
DIFS = 32
TF_SIZE = 89
DATA_RATE = 1
BA_SIZE = 32
DTI = 32  # Data Transmission Interval 시간, 단위: us

# 기본 설정 파라미터 값
MIN_OCW = 8  # 최소 백오프 카운터
MAX_OCW = 64  # 최대 백오프 카운터
RETRY_BS = 10  # 백오프 스테이지 최댓값

# Transmission time in us
TF_SZ_us = (TF_SIZE * 8) / (DATA_RATE * 1000)  # 트리거 프레임 전송 시간, 단위: us
BA_SZ_us = (BA_SIZE * 8) / (DATA_RATE * 1000)  # 블록 ACK 전송 시간, 단위: us
TWT_INTERVAL = DIFS + TF_SZ_us + SIFS * 2 + DTI + BA_SZ_us  # 전체 TWT 시간

# 성능 변수
Stats_PKT_TX_Trial = 0  # 전송 시도 수
Stats_PKT_Success = 0  # 전송 성공 수
Stats_PKT_Collision = 0  # 충돌 발생 수
Stats_PKT_Delay = 0  # 패킷 당 전송 시도 DTI 수

Stats_RU_TX_Trial = 0  # 전송 시도 수
Stats_RU_Idle = 0  # 빈 RU 수
Stats_RU_Success = 0  # 전송 성공 RU 수
Stats_RU_Collision = 0  # 충돌 발생 RU 수

stationList = []

PKS_throughput_results = []
PKS_coll_results = []
PKS_dealy_results = []
RU_idle_results = []
RU_Success_results = []
RU_coll_results = []

x_list = []

class Station:
    def __init__(self):
        self.ru = 0  # 할당된 RU
        self.cw = MIN_OCW  # 초기 OCW
        self.bo = random.randrange(0, self.cw)  # 백오프 카운터
        self.tx_status = False  # 전송 시도 여부
        self.suc_status = False  # 전송 성공 여부
        self.delay = 0
        self.retry = 0
        self.data_size = 0  # 데이터 크기 (바이트)

def createSTA(USER, packet_size):
    for i in range(USER):
        sta = Station()
        sta.data_size = packet_size
        stationList.append(sta)

def allocationRA_RU():
    for sta in stationList:
        if sta.bo <= 0:
            sta.tx_status = True
            sta.ru = random.randrange(0, NUM_RU)
        else:
            sta.bo -= NUM_RU
            sta.tx_status = False

def setSuccess(ru):
    for sta in stationList:
        if sta.tx_status and sta.ru == ru:
            sta.suc_status = True

def setCollision(ru):
    for sta in stationList:
        if sta.tx_status and sta.ru == ru:
            sta.suc_status = False

def incRUTX():
    global Stats_RU_TX_Trial
    Stats_RU_TX_Trial += 1

def incRUCollision():
    global Stats_RU_Collision
    Stats_RU_Collision += 1

def incRUSuccess():
    global Stats_RU_Success
    Stats_RU_Success += 1

def incRUIdle():
    global Stats_RU_Idle
    Stats_RU_Idle += 1

def checkCollision():
    coll_RU = [0] * NUM_RU
    for sta in stationList:
        if sta.tx_status:
            coll_RU[sta.ru] += 1

    for i in range(NUM_RU):
        incRUTX()
        if coll_RU[i] == 1:
            setSuccess(i)
            incRUSuccess()
        elif coll_RU[i] == 0:
            incRUIdle()
        else:
            setCollision(i)
            incRUCollision()

def addStats():
    global Stats_PKT_TX_Trial, Stats_PKT_Success, Stats_PKT_Collision, Stats_PKT_Delay

    for sta in stationList:
        if sta.tx_status:
            Stats_PKT_TX_Trial += 1
            if sta.suc_status:
                Stats_PKT_Success += 1
                Stats_PKT_Delay += sta.delay
            else:
                Stats_PKT_Collision += 1

def incTrial():
    for sta in stationList:
        sta.delay += 1

def changeStaVariables():
    for sta in stationList:
        if sta.tx_status:
            if sta.suc_status:
                sta.ru = 0
                sta.cw = MIN_OCW
                sta.bo = random.randrange(0, sta.cw)
                sta.tx_status = False
                sta.suc_status = False
                sta.delay = 0
                sta.retry = 0
                sta.data_size = 0
            else:
                sta.ru = 0
                sta.retry += 1
                if sta.retry >= RETRY_BS:
                    sta.cw = MIN_OCW
                    sta.retry = 0
                    sta.delay = 0
                    sta.data_size = 0
                else:
                    sta.cw = min(sta.cw * 2, MAX_OCW)
                sta.bo = random.randrange(0, sta.cw)
                sta.tx_status = False
                sta.suc_status = False

def print_Performance():
    PKS_coll_rate = (Stats_PKT_Collision / Stats_PKT_TX_Trial) * 100
    PKS_throughput = (Stats_PKT_Success * PACKET_SIZE * 8) / (NUM_SIM * NUM_DTI * TWT_INTERVAL)
    PKS_delay = (Stats_PKT_Delay / Stats_PKT_Success) * TWT_INTERVAL

    RU_idle_rate = (Stats_RU_Idle / Stats_RU_TX_Trial) * 100
    RU_Success_rate = (Stats_RU_Success / Stats_RU_TX_Trial) * 100
    RU_Collision_rate = (Stats_RU_Collision / Stats_RU_TX_Trial) * 100

    performance_dict = {
        "PKT_TX_Trial": Stats_PKT_TX_Trial,
        "PKT_Success": Stats_PKT_Success,
        "PKT_Collision": Stats_PKT_Collision,
        "PKT_Coll_Rate": PKS_coll_rate,
        "PKT_Throughput": PKS_throughput,
        "PKT_Delay": Stats_PKT_Delay / Stats_PKT_Success,
        "PKT_Delay_Time": PKS_delay,
        "RU_TX_Trial": Stats_RU_TX_Trial,
        "RU_Success": Stats_RU_Success,
        "RU_Collision": Stats_RU_Collision,
        "RU_Idle": Stats_RU_Idle,
        "RU_Idle_Rate": RU_idle_rate,
        "RU_Success_Rate": RU_Success_rate,
        "RU_Collision_Rate": RU_Collision_rate
    }

    return performance_dict

def run_simulation(bandwidth, tones, packet_sizes, output_file_csv):
    global NUM_RU, PACKET_SIZE, TWT_INTERVAL
    throughput_per_user = {}
    best_performance_overall = None

    for tone in tones:
        NUM_RU = tone

        for packet_size in packet_sizes:
            PACKET_SIZE = packet_size
            PKT_SZ_us = (PACKET_SIZE * 8) / (DATA_RATE * 1000)  # 데이터 패킷 전송 시간, 단위: us
            TWT_INTERVAL = DIFS + TF_SZ_us + SIFS * 2 + DTI + BA_SZ_us + PKT_SZ_us  # TWT 시간 재계산

            throughput_per_user[(tone, packet_size)] = []
            best_performance = None

            for i in range(1, USER_MAX + 1):
                print(
                    f"Running simulation for bandwidth {bandwidth} MHz, tone {tone}, packet size {packet_size}, number of users {i}")
                result_clear()  # 결과들 초기화하는 함수
                for k in range(0, NUM_SIM):  # 시뮬레이션 횟수
                    stationList.clear()  # stationlist 초기화
                    createSTA(i, packet_size)  # User의 수가 1일 때부터 500일 때까지 반복
                    for j in range(0, NUM_DTI):
                        incTrial()
                        allocationRA_RU()
                        checkCollision()
                        addStats()
                        changeStaVariables()
                performance = print_Performance()  # 성능 출력 및 결과 수집
                throughput_per_user[(tone, packet_size)].append(performance["PKT_Throughput"])

                if best_performance is None or performance["PKT_Throughput"] > best_performance["PKT_Throughput"]:
                    best_performance = performance
                    best_performance["Optimal User Count"] = i

            # 최적의 성능 결과를 저장
            if best_performance:
                best_performance.update({
                    "Bandwidth": bandwidth,
                    "Tone": tone,
                    "Optimal Packet Size": packet_size,
                    "Max Throughput": best_performance["PKT_Throughput"],
                })
                # 결과를 지속적으로 CSV 파일에 저장
                df = pd.DataFrame([best_performance])
                df.to_csv(output_file_csv, mode='a', header=not os.path.exists(output_file_csv), index=False)

    return throughput_per_user

def result_clear():
    global Stats_PKT_TX_Trial, Stats_PKT_Success, Stats_PKT_Collision, Stats_PKT_Delay
    global Stats_RU_TX_Trial, Stats_RU_Idle, Stats_RU_Success, Stats_RU_Collision

    Stats_PKT_TX_Trial = 0
    Stats_PKT_Success = 0
    Stats_PKT_Collision = 0
    Stats_PKT_Delay = 0
    Stats_RU_TX_Trial = 0
    Stats_RU_Idle = 0
    Stats_RU_Success = 0
    Stats_RU_Collision = 0

def plot_results(throughput_per_user, output_dir):
    for key, throughputs in throughput_per_user.items():
        tone, packet_size = key
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, USER_MAX + 1), throughputs, marker='o', linestyle='-', color='b')
        plt.title(f'Tone: {tone}, Packet Size: {packet_size} bytes')
        plt.xlabel('Number of Users')
        plt.ylabel('Throughput (Mbps)')
        plt.grid(True)

        file_name = f'tone_{tone}_packetsize_{packet_size}.png'
        plt.savefig(os.path.join(output_dir, file_name))
        plt.close()

def main():
    bandwidths = [20]  # 20 MHz
    tones_dict = {
        20: [26, 52, 106, 242]  # 20 MHz에서의 톤
    }
    packet_sizes = [500, 1000, 1500]  # 패킷 크기

    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file_csv = os.path.join(current_dir, "simulation_results_20MHz1.csv")
    output_file_npy = os.path.join(current_dir, "data_size_simulation_20MHz1.npy")
    output_dir = os.path.join(current_dir, "plots1_20MHz")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    throughput_per_user = {}

    for bandwidth in bandwidths:
        print(f"Running simulations for bandwidth {bandwidth} MHz")
        tones = tones_dict[bandwidth]
        throughput_per_tone = run_simulation(bandwidth, tones, packet_sizes, output_file_csv)
        throughput_per_user.update(throughput_per_tone)

    np.save(output_file_npy, throughput_per_user)
    print(f"\nSimulation list saved to {output_file_npy}")

    plot_results(throughput_per_user, output_dir)
    print(f"\nGraphs saved to {output_dir}")

if __name__ == "__main__":
    main()
