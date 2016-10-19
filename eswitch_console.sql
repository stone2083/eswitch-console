create database if not exists eswitch_console
default character set = utf8;

grant all on eswitch_console.* to 'eswitch'@'localhost' identified by 'eswitch';
grant all on eswitch_console.* to 'eswitch'@'*' identified by 'eswitch';

create table if not exists application (
    id int not null auto_increment comment 'primary key',
    name varchar(64) not null comment 'application\'s name',
    description varchar(256) default null comment 'application\'s description',
    create_date datetime not null comment 'create date',
    update_date datetime not null comment 'update date',
    primary key (id),
    unique key uni_name (name)
) default charset=utf8 comment 'application';

create table if not exists item (
    id int not null auto_increment comment 'primary key',
    app_id int not null comment 'application\'s id',
    app_name varchar(64) not null comment 'application\'s name',
    name varchar(64) not null comment 'item\'s name',
    description varchar(256) default null comment 'item\'s description',
    `on` tinyint not null default 0 comment 'item on/off flag',
    threshold int not null default 0 comment 'item threshold',
    detail varchar(1024) default null comment 'item detail',
    create_date datetime not null comment 'create date',
    update_date datetime not null comment 'update date',
    primary key (id),
    unique key uni_name (name)
) default charset=utf8 comment 'item';

create table if not exists instance (
    id int not null auto_increment comment 'primary key',
    app_id int not null comment 'application\'s id',
    app_name varchar(64) not null comment 'application\'s name',
    host varchar(32) not null comment 'app instance\'s host address',
    port int not null comment 'app instance\'s port',
    status tinyint not null comment 'app instance\'s status',
    last_ack datetime not null comment 'app instance last ack time',
    create_date datetime not null comment 'create date',
    update_date datetime not null comment 'update date',
    primary key (id),
    unique key uni_instance (app_name, host, port)
) default charset=utf8 comment 'application instance';

create table if not exists item_notify (
    id int not null auto_increment comment 'primary key',
    item_id int not null comment 'item\'s id',
    status tinyint not null comment 'item notify\'s status 0:fail, 1:success, 2:part success',
    detail varchar(1024) not null comment 'item notify\'s detail',
    create_date datetime not null comment 'create date',
    update_date datetime not null comment 'udpate date',
    primary key (id),
    unique uni_item_id (item_id)
) default charset=utf8 comment 'item notify';
