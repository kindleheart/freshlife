$(function () {
    // 得到商品价格
    var priceStr = $('#span1').text();
    var price = parseFloat(priceStr.substring(1));

    // 减少
    $('#reduced').click(function () {
        var count = $('#qty').val();
        count = parseInt(count);
        if(count > 1 ) {
            count--;
            $('#qty').val(count);
        }
        var total = count * price;
        // 保留两位小数
        $('#span5').text(total.toFixed(2) + '元');
    });
    // 增加
    $('#increase').click(function () {
        var count = $('#qty').val();
        count = parseInt(count);
        count++;
        $('#qty').val(count);
        var total = count * price;
        // 保留两位小数
        $('#span5').text(total.toFixed(2) + '元');
    });
    // 手动输入
    $('#qty').blur(function () {
        var count = $('#qty').val();
        // 校验count是否合法
        if(isNaN(count) || count.trim().length ==0 || parseInt(count) <= 0) {
            count = 1;
        }
        count = parseInt(count);
        $(this).val(count);
        var total = count * price;
        // 保留两位小数
        $('#span5').text(total.toFixed(2) + '元');
    });

    // 添加购物车
    $('.add_cart').click(function () {
        sku_id = $(this).attr('sku_id');
        count = $('#qty').val();
        csrf = $('input[name="csrfmiddlewaretoken"]').val();
        params ={'sku_id': sku_id, 'count': count, 'csrfmiddlewaretoken': csrf};
        $.post('/cart/add', params, function (data) {
            if (data.res == 5) {
                // alert(data.message);
                window.location.href = '/cart/info';
            } else {
                alert(data.errmsg);
            }
        });
    });


    $('#desc').click(function () {
        $('#comment').removeClass('active');
        $(this).addClass('active');
        $('#goods-desc').show();
        $('#goods-comment').hide()
    });
    $('#comment').click(function () {
        $('#desc').removeClass('active');
        $(this).addClass('active');
        $('#goods-desc').hide();
        $('#goods-comment').show()
    });
});