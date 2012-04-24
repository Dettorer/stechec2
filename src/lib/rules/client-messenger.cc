#include "client-messenger.hh"

#include <utils/log.hh>
#include <net/message.hh>

namespace rules {

ClientMessenger::ClientMessenger(net::ClientSocket_sptr sckt)
    : sckt_(sckt)
{
}

void ClientMessenger::send(const utils::Buffer& buf)
{
    utils::Buffer out_buf;
    net::Message msg(net::MSG_RULES);

    msg.handle_buffer(out_buf);
    out_buf += buf;

    sckt_->send(out_buf);
}

utils::Buffer* ClientMessenger::recv()
{
    utils::Buffer* buf = sckt_->recv();

    net::Message msg;
    msg.handle_buffer(*buf);

    return buf;
}

utils::Buffer* ClientMessenger::pull()
{
    utils::Buffer* buf = sckt_->pull();

    net::Message msg;
    msg.handle_buffer(*buf);

    return buf;
}

void ClientMessenger::wait_for_ack()
{
    utils::Buffer* buf = sckt_->recv();

    net::Message msg;
    msg.handle_buffer(*buf);

    CHECK_EXC(ClientMessengerError, msg.type == net::MSG_ACK);
}

} // namespace rules