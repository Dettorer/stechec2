#include "server-socket.hh"

#include <memory>
#include <zmq.hpp>

#include <utils/log.hh>

namespace net {

ServerSocket::ServerSocket(const std::string& pub_addr,
                           const std::string& rep_addr)
    : Socket(pub_addr, rep_addr, 2)
{
}

void ServerSocket::init()
{
    try
    {
        pubsub_sckt_ =
            std::shared_ptr<zmq::socket_t>(new zmq::socket_t(ctx_, ZMQ_PUB));
        pubsub_sckt_->bind(pubsub_addr_.c_str());
    }
    catch (const zmq::error_t& e)
    {
        FATAL("PUB: %s: %s", pubsub_addr_.c_str(), e.what());
    }

    try
    {
        reqrep_sckt_ =
            std::shared_ptr<zmq::socket_t>(new zmq::socket_t(ctx_, ZMQ_REP));
        reqrep_sckt_->bind(reqrep_addr_.c_str());
    }
    catch (const zmq::error_t& e)
    {
        FATAL("REP: %s: %s", reqrep_addr_.c_str(), e.what());
    }

    shared_init();
}

void ServerSocket::close()
{
    try
    {
        pubsub_sckt_->close();
    }
    catch (const zmq::error_t& e)
    {
        FATAL("SUB: close: %s", e.what());
    }

    try
    {
        reqrep_sckt_->close();
    }
    catch (const zmq::error_t& e)
    {
        FATAL("REQ: close: %s", e.what());
    }
}

bool ServerSocket::push(const utils::Buffer& buf, int flags)
{
    return send_sckt(buf, pubsub_sckt_, flags);
}

} // namespace net
