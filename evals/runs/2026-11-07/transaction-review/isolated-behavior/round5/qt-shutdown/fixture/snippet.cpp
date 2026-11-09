// 合成审查片段，并非可直接构建的完整工程。
class Worker : public QObject {
public:
    std::function<void(QString)> onResult;
    void run() { auto r = sdk.blockingRead(); onResult(r); }
};
void Window::start() {
    worker = new Worker(this);
    worker->moveToThread(&thread);
    worker->onResult = [this](QString r) { label->setText(r); };
    connect(&thread, &QThread::started, worker, &Worker::run);
    thread.start();
}
void Window::closeEvent(QCloseEvent *event) {
    thread.requestInterruption();
    thread.quit();
    thread.wait();
    delete worker;
    event->accept();
}
