$(function () {
    // 计算被选中的商品的总件数和总价格
    function updae_page_info() {
        // 获取被选中商品的checkbox
        total_count = 0;
        total_price = 0;
        $('.cart_list_td').find(':checked').parents('ul').each(function () {
            var count = $(this).find('.num_show').val();
            var amount = $(this).children('.col07').text();
            count = parseInt(count);
            amount = parseFloat(amount);
            total_count += count;
            total_price += amount;
        });
        $('.settlements').find('em').text(total_price.toFixed(2));
        $('.settlements').find('b').text(total_count);
    }

    // 计算商品的小计
    function update_goods_amount(sku_ul) {
        count = sku_ul.find('.num_show').val();
        price = sku_ul.children('.col05').text();
        count = parseInt(count);
        price = parseFloat(price);
        amount = count * price;
        sku_ul.children('.col07').text(amount.toFixed(2) + '元');
    }

    // 商品全选全不选
    $('.settlements').find(':checkbox').change(function () {
        //获取全选checkboxd的状态
        is_checked = $(this).prop('checked') ;
        $('.cart_list_td').find(':checkbox').each(function () {
           $(this).prop('checked', is_checked);
        });
        // 更新页面信息
        updae_page_info()
    });

    // 商品对应的checkbox状态发送改变
    $('.cart_list_td').find(':checkbox').change(function () {
        // 获取页面上所有商品的数目
        all_len = $('.cart_list_td').length;
        // 获取页面上被选中商品的数目
        checked_len = $('.cart_list_td').find(':checked').length;
        is_checked = true;
        if (checked_len < all_len) {
            is_checked = false;
        }
        $('.settlements').find(':checkbox').prop('checked', is_checked);
        // 更新页面信息
        updae_page_info()
    });

    error_update = false;
    total = 0;
    // 更新购物车中商品的数量
    function update_remote_cart_info(sku_id, count) {
        csrf = $('input[name="csrfmiddlewaretoken"]').val();
        params = {
            'sku_id': sku_id,
            'count': count,
            'csrfmiddlewaretoken': csrf
        };
        // 设置ajax请求为同步
        $.ajaxSettings.async = false;
        $.post("/cart/update", params, function (data) {
            if (data.res == 5) {
                error_update = false;
                total = data.total_count;
            } else {
                alert(data.errmsg);
                error_update = true;
            }
        });
        $.ajaxSettings.async = true;
    }

    // 购物车商品增加
    $('.add').click(function () {
       //获取商品id和商品数量
        sku_id = $(this).next().attr('sku_id');
        count = $(this).next(). val();
        count = parseInt(count) + 1;

       // 更新购物车中的数量
        update_remote_cart_info(sku_id, count);

        if (error_update == false) {
            // 重新设置商品数目
            $(this).next().val(count);
            // 计算商品的小计
            update_goods_amount($(this).parents('ul'));
            // 获取对应的checkbox的选中状态，如果被选择，更新页面信息
            is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
            if (is_checked) {
                updae_page_info();
            }
            // 更新页面上购物车的总件数
            $('.total_count').children('em').text(total);
        }
    });

    // 购物车商品减少
    $('.minus').click(function () {
       //获取商品id和商品数量
        sku_id = $(this).prev().attr('sku_id');
        count = $(this).prev(). val();
        count = parseInt(count) - 1;
        if(count <= 0) return;

        // 更新购物车中的数量
        update_remote_cart_info(sku_id, count);

        if (error_update == false) {
            // 重新设置商品数目
            $(this).prev().val(count);
            // 计算商品的小计
            update_goods_amount($(this).parents('ul'));
            // 获取对应的checkbox的选中状态，如果被选择，更新页面信息
            is_checked = $(this).parents('ul').find(':checkbox').prop('checked');
            if (is_checked) {
                updae_page_info();
            }
            // 更新页面上购物车的总件数
            $('.total_count').children('em').text(total);
        }
    });

    // 记录用户输入之前商品的数量
    pre_count = 0;
    $('.num_show').focus(function () {
        pre_count = $(this).val()
    });

    // 用户手动输入
    $('.num_show').blur(function () {
       //获取商品id和商品数量
        sku_id = $(this).attr('sku_id');
        count = $(this).val();

        if(isNaN(count) || count.trim().length == 0 || parseInt(count) <= 0) {
            // 设置商品的数量为用户之前的数目
            $(this).val(pre_count);
            return;
        }

        // 更新购物车中的数量
        count = parseInt(count);
        update_remote_cart_info(sku_id, count);

        if (error_update == false) {
            // 重新设置商品数目
            $(this).val(count);
            // 计算商品的小计
            update_goods_amount($(this).parents('ul'));
            // 获取对应的checkbox的选中状态，如果被选择，更新页面信息
            is_checked = $(this).parents('ul').find(':checkbox').prop('checked');
            if (is_checked) {
                updae_page_info();
            }
            // 更新页面上购物车的总件数
            $('.total_count').children('em').text(total);
        } else {
            // 更新失败,恢复到原来的值
            $(this).val(pre_count);
        }
    });

    // 删除购物车中的记录
    $('.cart_list_td').children('.col08').children('a').click(function () {
        res = confirm('确认删除该商品?');
        if(res == false) return;
        // 获取对应商品的id
        sku_id = $(this).parents('ul').find('.num_show').attr('sku_id');
        csrf = $('input[name="csrfmiddlewaretoken"]').val();
        params = {
            'sku_id': sku_id,
            'csrfmiddlewaretoken': csrf
        };
        // 获取商品所在的ul
        sku_ul = $(this).parents('ul');
        $.post('/cart/delete', params, function (data) {
            if(data.res == 3) {
                //移除页面上的商品所在的ul元素
                sku_ul.remove();
                // 获取sku_ul中的选中状态
                is_checked = sku_ul.find(':checked').prop('checked');
                if(is_checked) {
                    updae_page_info();
                }
                // 更新页面上购物车的总件数
                $('.total_count').children('em').text(data.total_count);
                // 更新页面上购物车数量
                cart_count = $('#show_count').text();
                cart_count = parseInt(cart_count) - 1;
                $('#show_count').text(cart_count);
            } else {
                alert(data.errmsg);
            }
        });
    });


});