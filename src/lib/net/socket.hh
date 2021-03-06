#ifndef LIB_NET_SOCKET_HH_
# define LIB_NET_SOCKET_HH_

# include <string>
# include <memory>
# include <zmq.hpp>
# include <utils/buffer.hh>

namespace net {

const int SCKT_NOBLOCK = ZMQ_DONTWAIT;

struct Message;

// Socket is the common representation of the pair of ZeroMQ sockets Stechec
// needs to work. It is composed of the ZeroMQ context a PUB-SUB socket and
// a REQ-REP socket

class Socket // abstract
{
public:
    Socket(const std::string& pubsub_addr,
           const std::string& reqrep_addr,
           int io_thread);

    virtual ~Socket() {}

    virtual void init() { shared_init(); }
    virtual bool send(const utils::Buffer& msg, int flags = 0);
    virtual utils::Buffer* recv(int flags = 0);
    virtual bool poll(long timeout);
    virtual void close() = 0;

protected:
    bool send_sckt(const utils::Buffer& buf,
            std::shared_ptr<zmq::socket_t> sckt, int flags);
    // recv_sckt allocates a Message, it has to be deleted after its use
    utils::Buffer* recv_sckt(std::shared_ptr<zmq::socket_t> sckt, int flags);

protected:
    // Must be called by subclasses after custom initialization.
    void shared_init();

    std::string pubsub_addr_;
    std::string reqrep_addr_;

    zmq::context_t ctx_;
    std::shared_ptr<zmq::socket_t> pubsub_sckt_;
    std::shared_ptr<zmq::socket_t> reqrep_sckt_;
};

} // namespace net

#endif // !LIB_NETWORK_SOCKET_HH_
