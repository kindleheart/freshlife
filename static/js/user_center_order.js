$(function () {
    $('.btn_pay').click(function () {
        status = $(this).attr('status');
        if(status == 1) {
            // 进行支付
            order_id = $(this).attr('order_id');
            csrf = $('input[name="csrfmiddlewaretoken"]').val();
            params = {
                'order_id': order_id,
                'csrfmiddlewaretoken': csrf
            };
            $.post('/order/pay', params, function (data) {
                if(data.res == 3) {
                    // 引导用户到支付页面
                    window.open(data.pay_url);
                } else {
                    alert(data.errmsg)
                }
            })
        } else {


        }
    });
});